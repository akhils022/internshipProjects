# Lambda function that adds a CSV document into an SQL database
import os
import json
import logging
from sqlalchemy import create_engine
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create the SQLAlchemy engine
engine = create_engine(os.environ.get("SQL_CONNECTION_STRING"))
try:
    with engine.connect() as connection:
        logger.info("Connection successful!")
except Exception as e:
    logger.info(f"Error occurs when connecting to the database: {e}")

def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))

    # Grab table name and data from request
    name = event.get("pathParameters")["name"]
    df = pd.DataFrame(json.loads(event.get("body")))

    # Insert into database using pandas
    try:
        df.to_sql(name, engine, if_exists='append', index=False)
        # Return success
        return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": "Success"
            }
    except Exception as e:
        # Return failure if exception
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": f"Error: {str(e)}"
            })
        }