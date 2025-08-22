"""
Tools for PowerBI queries.
"""

import os
import time
import logging
import requests
from google.cloud import storage
import json

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

access_token = None

# Helper function to reconnect to PowerBI data source
def reconnect():
    try:
        # Generate Authentication Token
        url = f"https://login.microsoftonline.com/{os.environ.get('TENANT_ID')}/oauth2/v2.0/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        body = {
            "grant_type": "client_credentials",
            "client_id": os.environ.get('CLIENT_ID'),
            "client_secret": os.environ.get('CLIENT_SECRET'),
            "scope": "https://analysis.windows.net/powerbi/api/.default"
        }
        print(url)
        print(body)
        response = requests.post(url, data=body, headers=headers)
        response.raise_for_status()

        # Return generated access token
        return response.json()['access_token']
    except Exception as e:
        logger.info(f"Error reconnecting to PowerBI: {str(e)}")
        return None

# Helper Function to execute a DAX query in a PowerBI data source
def request_data(query, access_token):
    # Generate API url to execute query
    url = f"https://api.powerbi.com/v1.0/myorg/datasets/{os.environ.get('DATASET_ID')}/executeQueries"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    body = {
        "queries": [{"query": query}],
        "serializerSettings": {"includeNulls": True}
    }

    t = time.time()
    # Execute the query
    response = requests.post(url, data=json.dumps(body), headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return {
            "status": "error",
            "message": f"Error querying PowerBI data source: {str(http_err)}",
            "result": "",
        }

    # Return the usable results
    logger.info(f"DAX Query Time: {time.time() - t:.3f} seconds")
    return response.json()['results'][0]['tables'][0]['rows']

def powerbi_metadata():
    """
    Return table schema, relationships, and measures in a PowerBI dataset.

    Returns:
        dict: The metadata, in a structured, detailed format
    """

    try:
        bucket = storage.Client().get_bucket("timesquare-retail")

        # Get data for tables
        blobs = bucket.list_blobs(prefix="tables/")
        tables_data = {}
        for blob in blobs:
            if blob.name.endswith(".tmdl"):  # Only process .tmdl files
                try:
                    tables_data[blob.name] = blob.download_as_text()
                except Exception as e:
                    logger.error(f"Error processing {blob.name}: {e}")

        # Get data for measures
        blobs = bucket.list_blobs(prefix="measures/")
        measures_data = {}
        for blob in blobs:
            if blob.name.endswith(".tmdl"):  # Only process .tmdl files
                try:
                    measures_data[blob.name] = blob.download_as_text()
                except Exception as e:
                    logger.error(f"Error processing {blob.name}: {e}")

        # Get relationship data
        rel = bucket.blob("relationships.tmdl").download_as_text()

        logger.info(f"Successfully retrieved PowerBI metadata")
        return {
            "status": "success",
            "message": f"Succefully retrieved PowerBI metadata",
            "tables": tables_data,
            "measures": measures_data,
            "relationships": rel,
        }
    except Exception as e:
        logger.error(f"Error retrieving PowerBI metadata: {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving PowerBI metadata: {str(e)}",
            "result": "",
        }

def dax_query(
        query: str,
) -> dict:

    """
    Query an PowerBI database with the provided string and return relevant results.

    Args:
        query (str): The DAX query in string format to use

    Returns:
        dict: The status and query results
    """

    global access_token
    if not access_token:
        logger.info("No access token found, retrieving new token...")
        access_token = reconnect()
        if not access_token:
            return {
                "status": "error",
                "message": "Failed to get access token during initialization.",
                "result": ""
            }

    # Connect and execute DAX query
    try:
        result = request_data(query, access_token)
        logger.info(f"Successfully queried: {query}")
        return {
            "status": "success",
            "message": f"Succefully queried {query} to PowerBI data source",
            "result": result,
        }
    except requests.exceptions.HTTPError as e:
        # Check if error is due to expired token (401 Unauthorized or 403 Forbidden)
        if e.response is not None and e.response.status_code in (401, 403):
            logger.info("Access token expired or unauthorized, refreshing token and retrying...")
            # Refresh token
            token = reconnect()
            if not token:
                return {
                    "status": "error",
                    "message": "Failed to refresh access token.",
                    "result": ""
                }
            try:
                # Retry with new token
                result = request_data(query, token)
                logger.info(f"Successfully queried after token refresh: {query}")
                return {
                    "status": "success",
                    "message": f"Successfully queried {query} to PowerBI data source after token refresh",
                    "result": result,
                }
            except Exception as retry_err:
                logger.error(f"Failed after token refresh: {retry_err}")
                return {
                    "status": "error",
                    "message": f"Failed querying after token refresh: {str(retry_err)}",
                    "result": ""
                }
        else:
            logger.error(f"Query failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Error querying PowerBI data source: {str(e)}",
                "result": ""
            }
    except Exception as e:
        logger.error(f"Unexpected error querying PowerBI data source: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error querying PowerBI data source: {str(e)}",
            "result": ""
        }
