# Web implementation of chatbot with RAG and SQL analytical features
import os
import streamlit as st
from dotenv import load_dotenv
import time
from helpersv2 import *
from agent import DSPyAgentApp
from powerbilocal import dax_query, powerbi_metadata

load_dotenv(override=True)
# Setting up Vertex Agent
# Persistent data
if "sessions" not in st.session_state:
    st.session_state.sessions = {0: {"name":f"New Session",
                                 "messages":[],
                                 "events": []}}
    st.session_state.agent = DSPyAgentApp(
        name="dspy_agent",
        tools=[dax_query, powerbi_metadata],
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION"),
    )
    st.session_state.agent.set_up()
if "current_session" not in st.session_state:
    st.session_state.current_session = 0

# ---- Helper Functions for Chatbot Application ----
def query_bot(message):
    response = st.session_state.agent.query(message)
    print("Response:" + str(response))
    gs = []
    f = json.loads(response['charts']) if response['charts'] != '' else {}
    for g in f:
        print(g)
        gs.append((create_graph(f[g]), extract_table_from_graph(f[g])))
    return response['text'], gs

# Clear current chat without deleting session
def clear_chat():
    st.session_state.sessions[st.session_state.current_session]["messages"] = []

# Function to display chat history with graphs
def display_chat_history():
    st.title("🧠 Chat with Analytics Agent")
    for msg in st.session_state.sessions[st.session_state.current_session]["messages"]:
        # Display user message
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        # Display bot response
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                # Time and cost info
                st.markdown(f"""
                  <div style="display: flex; justify-content: flex-start; font-size: 12px; color: gray; margin-bottom: 10px;">
                      <span style="margin-right: 2em;">Time elapsed: {msg["time"]:.2f}s</span>
                      <span>Cost accrued: {msg["cost"]:.4f}</span>
                  </div> """, unsafe_allow_html=True)
                # Textual Response
                st.write(msg["content"])
                if msg["graphs"]:
                    for graph, table in msg.get("graphs", []):
                        # Display graph as html
                        st.components.v1.html(graph, height=500)
                        st.dataframe(table)

# Sidebar module for session manager
def sidebar():
    st.sidebar.title("🗂️ Session Manager")
    with st.sidebar.expander("Manager", expanded=True):
        # Buttons to manage session
        st.markdown(f""":gray[🔑 **Session Name:**]  
                      *{st.session_state.sessions[st.session_state.current_session]['name']}*
                      """)
        st.markdown(f""":green[💲 **Session Cost:**]
                    *{round(st.session_state.sessions[st.session_state.current_session].get("cost", 0), 5)}*
                    """)
        if st.button("♻️ Clear Chat", key="top_clear", type='primary'):
            clear_chat()

    st.sidebar.markdown("### 🗒️ Session List")
    # Rename current session
    if st.session_state.sessions:
        new_name = st.sidebar.text_input("New Name", st.session_state.sessions[st.session_state.current_session]["name"])
        if st.sidebar.button("Rename Session", type='primary', key='rename_session'):
            st.session_state.sessions[st.session_state.current_session]["name"] = new_name
            st.rerun()

    # List all sessions
    for sid in list(st.session_state.sessions.keys()):
        if sid != st.session_state.current_session:
            if st.sidebar.button(st.session_state.sessions[sid]["name"], key=sid, type='tertiary'):
                st.session_state.current_session = sid
                st.rerun()

    st.sidebar.markdown(f""":red[**Click session name to switch.**]""")
    st.sidebar.markdown("---")

    # Log agent events
    with st.sidebar.expander("📝 Event Logger", expanded=True):
        events = st.session_state.sessions[st.session_state.current_session]["events"]
        if events:
            for idx, event in enumerate(events):
                # Log events based on their type
                if 'function_call' in event['content']['parts'][0]:
                    with st.expander(f"**{idx}**: {event['content']['parts'][0].get('function_call').get('name', 'N/A')}"):
                        st.json(event)
                # Check if the event contains a function response
                elif 'function_response' in event['content']['parts'][0]:
                    with st.expander(f"**{idx}**: {event['content']['parts'][0].get('function_response').get('name', 'N/A')}"):
                        st.json(event)
                # For textual events
                elif 'text' in event['content']['parts'][0]:
                    text_output = event['content']['parts'][0].get('text')
                    with st.expander(f"**{idx}**: {text_output[:30] if len(text_output) > 30 else text_output}"):
                        st.json(event)
        else:
            st.markdown(f":blue[***Logged Session Events Appear Here***]")

# Display history and sidebar
if st.session_state.sessions:
    sidebar()
    display_chat_history()

# Ask for user query
prompt = st.chat_input("Type your query here...")
if prompt:
    # Display User message
    with st.chat_message("user"):
        st.write(prompt)
        st.session_state.sessions[st.session_state.current_session]["messages"].append({"role": "user", "content": prompt})

    # Query chatbot with user prompt and display response
    with st.chat_message("assistant"):
        t = time.time()
        with st.spinner("Thinking...", show_time=True):
            text, graphs = query_bot(prompt)
            tt = time.time() - t
            # Extract response and add to chat history
            st.markdown(f"""
              <div style="display: flex; justify-content: flex-start; font-size: 12px; color: gray; margin-bottom: 10px;">
                  <span style="margin-right: 2em;">Time elapsed: {tt:.2f}s</span>
                  <span>Cost accrued: {1}</span>
              </div> """, unsafe_allow_html=True)
            st.write(text)
            if graphs:
                for graph, table in graphs:
                    # Display graph as html
                    st.components.v1.html(graph, height=500)
                    st.dataframe(table)
            st.session_state.sessions[st.session_state.current_session]["messages"].append({"role": "assistant",
                                                                                            "content": text, "graphs": graphs, "cost": 1, "time": tt})
