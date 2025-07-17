# Program to test functionality of RAG agent and session service
from vertexai import agent_engines
from google.adk.sessions import VertexAiSessionService
from google import adk
from google.genai import types
from . import agent
import streamlit as st
import os

# Setting up Vertex Agent
app_name = os.environ.get("RESOURCE_ID")
remote_app = agent_engines.get(id)
session_service = VertexAiSessionService(
       os.environ.get("PROJECT_ID"), os.environ.get("LOCATION"))
runner = adk.Runner(
    agent=agent.root_agent,
    app_name=os.environ.get("RESOURCE_ID"),
    session_service=session_service)

# Persistent data
if "sessions" not in st.session_state:
  st.session_state.sessions = {0: {"name" : "Session 0",
                                    "messages" : []}}
if "current_session" not in st.session_state:
  st.session_state.current_session = 0
if "cur_id" not in st.session_state:
  st.session_state.cur_id = 0
 

# Helper function to get a response from the bot
def query_bot(message, session_id, user_id):
  content = types.Content(role='user', parts=[types.Part(text=message)])
  events = runner.run(
      user_id=user_id, session_id=session_id, new_message=content)

  for event in events:
      if event.is_final_response():
          final_response = event.content.parts[0].text
          print("Agent Response: ", final_response)

# Create a session and run test queries
session = session_service.create_session(
       app_name=app_name,
       user_id="user")

query_bot("Hello, how are you!", session.id, "user")
# Test session memory
query_bot("What did I say before?", session.id, "user")