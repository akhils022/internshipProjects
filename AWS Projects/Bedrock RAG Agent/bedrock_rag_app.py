# Streamlit app for a Retrieval Augmented Generation (RAG) AI Chatbot
import streamlit as st
import rag_helper

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Title
st.title("Bedrock Knowledge Base Chatbot")

# Chat interface section
with st.expander("Chat with Bot Here 🤖", expanded=True):
    # Render message history so far with correct roles
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])
    # Wait for user input
    input_text = st.chat_input("Chat with the RAG bot here")

    # Add user input to message history and send to RAG bot
    if input_text:
        with st.chat_message("user"):
            st.markdown(input_text)
        st.session_state.chat_history.append({"role": "user", "text": input_text})

        # Grab response with RAG API
        with st.spinner("Fetching response from knowledge base..."):
            response_content = rag_helper.retrieveAndGenerate(input_text)['output']['text']
        # Add response to history and render in chat
        with st.chat_message("assistant"):
            st.markdown(response_content)
        st.session_state.chat_history.append({"role": "assistant", "text": response_content})

# Other functions to manage chat and knowledge base
with st.expander("📁 Manage Knowledge Base or Clear Chat", expanded=True):
    file = st.file_uploader(label='Click to upload file')
    # If file uploaded, add to data source bucket
    if file is not None:
        if st.button('Upload file', key="upload_file"):
            rag_helper.uploadToS3(file, file.name)
            st.success("File Uploaded")

    # Sync data source with knowledge base when user confirms
    if st.button("Press when done to update knowledge base", key="update_kb"):
        with st.spinner("Updating knowledge base..."):
            rag_helper.updatekb()

    # If user clears chat, wipe message history
    if st.button("Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()