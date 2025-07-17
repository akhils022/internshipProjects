# Web implementation of chatbot with RAG and SQL analytical features
import os
import vertexai
from vertexai import agent_engines
import streamlit as st
from dotenv import load_dotenv
import json
import plotly.graph_objs as go

load_dotenv()
# Setting up Vertex Agent
vertexai.init(
    project=os.environ.get("PROJECT_ID"),
    location=os.environ.get("LOCATION"),
    staging_bucket=os.environ.get("BUCKET_ID"),
)
remote_app = agent_engines.get(os.environ.get("RESOURCE_ID"))
user_id = os.environ.get("USER_ID")
 
# ---- Helper Functions ----

# Gets a response from the bot
def query_bot(session_id, message):
  final_response = None
  for event in remote_app.stream_query(
    user_id=user_id,
    session_id=session_id,
    message=message
  ):
    # Print event for debugging
    print(event)
    final_response = event
  if "content" in final_response and "parts" in final_response["content"] and "text" in final_response["content"]["parts"][0]:
    return final_response["content"]["parts"][0]["text"]
  else:
    return "No response from AI Engine"

# Create new session
def new_session():
  session = remote_app.create_session(user_id=user_id)
  st.session_state.current_session = session['id']
  st.session_state.sessions[session['id']] = {"name":f"New Session",
                                                        "messages":[]}
# Delete current session
def delete_session():
  del st.session_state.sessions[st.session_state.current_session]
  if st.session_state.sessions:
    st.session_state.current_session = list(st.session_state.sessions.keys())[-1]
  else:
    new_session()

# Clear current chat without deleting session
def clear_chat():
  st.session_state.sessions[st.session_state.current_session]["messages"] = []

# Uses HighCharts API to create a HTML graph
def create_graph(graph):
  return f"""
      <div id="container" style="width:100%; height:400px;"></div>
      <script src="https://code.highcharts.com/highcharts.js"></script>
      <script type="text/javascript">
          var chartData = {json.dumps(graph)};
          Highcharts.chart('container', chartData);
      </script>
  """

# Split a chatbot response into text and graphs
def split_response(response):
  start_index = response.find('```json\n') + len('```json\n')
  if start_index != -1:
      # Extract text and json data
      text = response[:response.find('```json\n')].strip()
      json_data = response[start_index:].split('```')[0].strip()
      try:
          # Load the JSON data
          data = json.loads(json_data)
          graphs = []
          for graph in data["graphs"]:
              # Create graph based on the data
              graphs.append(create_graph(data["graphs"][graph]))
          return text, graphs
      except json.JSONDecodeError:
          return text, None
  else:
      # If no graphs, return text only
      return response, None

# Function to display chat history with graphs
def display_chat_history():
  for msg in st.session_state.sessions[st.session_state.current_session]["messages"]:
    if msg["role"] == "user":
      with st.chat_message("user"):
        st.markdown(msg["content"])
    elif msg["role"] == "assistant":
      with st.chat_message("assistant"):
        st.markdown(msg["content"])
      if "graphs" in msg:
        for graph in msg['graphs']:
          # Display graph as html
          st.components.v1.html(graph, height=500)

# Persistent data
if "sessions" not in st.session_state:
  st.session_state.sessions = {}
if "current_session" not in st.session_state:
  st.session_state.current_session = 0
  new_session()

# ---------- Top Bar Layout ----------
with st.sidebar.expander("Session Manager", expanded=True):
  st.markdown(f""":gray[🔑 **Session Name**:]  
                *{st.session_state.sessions[st.session_state.current_session]['name']}*
                """)
  if st.button("➕ New Session", key="top_new"):
    new_session()
  if st.button("🗑️ Delete Session", key="top_delete", type='primary'):
    delete_session()
  if st.button("♻️ Clear Chat", key="top_clear", type='primary'):
    clear_chat()

# ------ Sidebar Info ------
st.sidebar.title("🗂️ Sessions")
# Rename current session
if st.session_state.sessions:
  new_name = st.sidebar.text_input("New Name", st.session_state.sessions[st.session_state.current_session]["name"])
  if (st.sidebar.button("Rename Session")):
    st.session_state.sessions[st.session_state.current_session]["name"] = new_name
    st.rerun()

# List all sessions
for sid in list(st.session_state.sessions.keys()):
  if sid != st.session_state.current_session:
    if st.sidebar.button(st.session_state.sessions[sid]["name"], key=sid, type='tertiary'):
      st.session_state.current_session = sid
      st.rerun()
st.sidebar.markdown("---")
st.sidebar.write("Click session name to switch.")

# ---- Chat Input Area ----
st.title("🧠 Chat with Business Analytics Agent")

display_chat_history()

# Ask for user query
prompt = st.chat_input("Type your query here...")
if prompt:
  st.session_state.sessions[st.session_state.current_session]["messages"].append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)
    # Query chatbot with user prompt
  with st.chat_message("assistant"):
    with st.spinner("Thinking..."):
      response = query_bot(st.session_state.current_session, prompt)
      text, graphs = split_response(response)
      st.markdown(text)
      # Append response and graphs if needed
      if (graphs):
        st.session_state.sessions[st.session_state.current_session]["messages"].append({"role": "assistant", "content": text, "graphs": graphs})
        for graph in graphs:
          st.components.v1.html(graph, height=500)
      else:
        st.session_state.sessions[st.session_state.current_session]["messages"].append({"role": "assistant", "content": text})
