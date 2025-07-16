import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda function
def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))
    s3 = boto3.client('s3')

    # Grab key from API request
    key = event.get('queryStringParameters')['key']
    logger.info("Fetching data from file key: " + key)
    # Retrieve metadata
    response = s3.head_object(Bucket='streamlits3test', Key=key)
    # Format response
    size = response.get('ContentLength')
    dt = response.get('LastModified')
    date = dt.strftime("%x")
    time = dt.strftime("%X")

    logger.info(f"File Info - Key: {key}, Size: {size}, Date: {date}, Time: {time}")

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": "{\"key\": \"" + key + "\", \"size\": " + str(size) + ", \"date\": \"" + date + "\", \"time\": \"" + time + "\"}"
    }