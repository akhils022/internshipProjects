# Functions to create and deploy and ADK agent
import os
from dotenv import load_dotenv, find_dotenv
import vertexai
from vertexai.preview import reasoning_engines
from rag_agent.agent import root_agent

load_dotenv(find_dotenv())

# Initialize VertexAI config
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION"),
    staging_bucket=os.environ.get("GOOGLE_CLOUD_STAGING_BUCKET"),
)

# Helper function to create the ADK agent with tools and dependencies
def createAgent():
  requirements = [
      "google-cloud-aiplatform[adk,agent_engines]",
      "cloud-sql-python-connector[pymysql]",
      "sqlalchemy",
      "python-dotenv",
      "pandas",
  ]

  extra_packages=["./rag_agent"]

  display_name = "RAG/SQL Agent for Business Analytics"
  description = "A helpful agent that can assist with analyzing business documents and database information."

  app = reasoning_engines.AdkApp(
      agent=root_agent,
      enable_tracing=True
  )
  remote_agent = vertexai.agent_engines.create(
      agent_engine=app,
      requirements=requirements,
      extra_packages=extra_packages,
      display_name=display_name,
      description=description,
  )

  print(f"Created remote agent, resource id: {remote_agent.resource_name}")

# Helper function to delete a deployment
def delete(resource_id: str) -> None:
  """Deletes an existing deployment."""
  remote_app = vertexai.agent_engines.get(resource_id)
  remote_app.delete(force=True)
  print(f"Deleted remote app: {resource_id}")

# Helper function to list all deployments
def list_deployments() -> None:
    """Lists all deployments."""
    deployments = vertexai.agent_engines.list()
    if not deployments:
        print("No deployments found.")
        return
    print("Deployments:")
    for deployment in deployments:
        print(f"- {deployment.resource_name}")