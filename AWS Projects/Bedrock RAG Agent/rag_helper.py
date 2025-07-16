# Helper module with bedrock and S3 functions
import boto3
import os

# Uploads a file to a dedicated S3 bucket
def uploadToS3(file, key):
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.upload_fileobj(file, 'mybedrockbucket011', key)

# Uses RAG API call to generate a response
def retrieveAndGenerate(input):
    bedrock_agent_runtime = boto3.client(
        service_name = "bedrock-agent-runtime",
                    region_name='us-east-1')
    return bedrock_agent_runtime.retrieve_and_generate(
        input={
            'text': input
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': os.environ.get("KNOWLEDGE_BASE_ID"),
                'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0'
                }
            }
        )

# Updates knowledge base by syncing with data source
def updatekb():
    bedrock_agent = boto3.client(
    service_name = "bedrock-agent",
                  region_name='us-east-1')
    bedrock_agent.start_ingestion_job(
      dataSourceId=os.environ.get("DATA_SOURCE_ID"),
      knowledgeBaseId=os.environ.get("KNOWLEDGE_BASE_ID"))
 