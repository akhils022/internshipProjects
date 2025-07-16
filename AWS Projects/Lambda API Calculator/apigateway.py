# File to integrate API Gateway with Lambda
import boto3

# Create a boto3 client
client = boto3.client('apigatewayv2')

# Create the API Gateway
response = client.create_api(
    Name='calc',
    ProtocolType='HTTP'
)
api_id = response['ApiId']
print(f"API Gateway created with ID: {api_id}")

# Lambda URI Redacted
lambda_uri = "arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME"

# Create Integration
integration_response = client.create_integration(
    ApiId=api_id,
    IntegrationType='AWS_PROXY',
    IntegrationUri=lambda_uri,
    PayloadFormatVersion='2.0'
)
integration_id = integration_response['IntegrationId']
print(f"Integration created with ID: {integration_id}")

# Create Route
client.create_route(
    ApiId=api_id,
    RouteKey='GET /calc',
    Target=f'integrations/{integration_id}'
)

# Create Stage
stage_name = "test"
client.create_stage(
    ApiId=api_id,
    StageName=stage_name
)

# Create Deployment
client.create_deployment(
    ApiId=api_id,
    StageName=stage_name
)

print(f"Deployment created for stage: {stage_name}")