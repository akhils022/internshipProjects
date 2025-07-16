# Lambda function that inserts a document into MongoDB
import json
import os
import logging
from pymongo import MongoClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Setup connection
client = MongoClient(os.environ.get("MONGO_CONNECTION_STRING"))
db = client['databaseproject']

def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))

    # Grab name of collection to add to
    collection = db[event.get("pathParameters")["name"]]
    data = json.loads(event.get("body"))

    # Insert the provided data into collection
    try:
        result = collection.insert_many(data)
        # Return success
        if result.inserted_ids:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "message": "Success",
                    "insertedCount": len(result.inserted_ids)
                })
            }
        else:
            # Return failure
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "message": "Insert operation failed"
                })
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": f"Error: {str(e)}"
            })
        }