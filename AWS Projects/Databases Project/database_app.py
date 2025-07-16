# Streamlit app for uploading CSV documents into MongoDB or an Amazon RDS SQL server
# Supports SQL queries after uploading
import os
import pandas as pd
import time
import requests
import numpy as np
import streamlit as st
from sqlalchemy import create_engine

# Helper function that uploads to the correct database
def upload(df, mongo):
    df = df.replace({np.nan: None})
    data = df.to_dict(orient='records')
    # Use API Gateway to route request to correct lambda function
    api_url = os.environ.get("API_URL")
    if (mongo):
        api_url += "mongo/"
    else:
        api_url += "sql/"
    api_url += st.session_state['name']
    # Attempt to upload document, return success or error if failure
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(api_url, json=data, headers=headers)
        if response.status_code == 200:
            st.success("Document uploaded successfully")
        else:
            st.error(f"Failed to upload data. Status code: {response.status_code}\nResponse: {response.text}")
    except Exception as e:
        print(e)
        st.error("Failed to upload document")

# Persistent variables that are preserved when app is reloaded
if 'finalized' not in st.session_state:
    st.session_state['finalized'] = False
if 'name' not in st.session_state:
    st.session_state['name'] = ""
if 'sql' not in st.session_state:
    st.session_state['sql'] = False

# Title region
st.title('Welcome to a CSV file editor and database uploader:')
st.header("Please upload a CSV file to edit/upload")
file = st.file_uploader(label='Upload CSV', type='.csv')

# Once file is uploaded, create a data editing interface
if file is not None:
    st.subheader(f"Editing {file.name}")
    df_edited = st.data_editor(pd.read_csv(file), num_rows='dynamic')

    # If user is ready, ask for a table or collection name    
    n = st.text_input("Enter The Collection/Table Name (no spaces)", file.name[:-4] + "_edited")

    # convert edited content to CSV file
    if st.button('Finalize Changes') and not st.session_state['finalized']:
        st.session_state['sql'] = False
        f = df_edited.to_csv(index=False)
        st.session_state['name'] = n.replace(' ', '_')

        success_msg = st.success(f"Changes finalized. Collection/Table name: {st.session_state['name']}")
        time.sleep(2)
        success_msg.empty()
        
        st.session_state['finalized'] = True

    # Show Upload buttons if changes have been finalized
    if st.session_state['finalized']:
        if st.button(label='Upload to MongoDB Atlas'):
            with st.spinner("Uploading to MongoDB Atlas..."):
                upload(df_edited, True)
                st.session_state['finalized'] = False
        elif st.button(label='Upload to Amazon RDS MySQL'):
            with st.spinner("Uploading to Amazon RDS MySQL"):
                upload(df_edited, False)
                st.session_state['finalized'] = False
                st.session_state['sql'] = True
            
else:
    st.warning('Please upload a CSV file to edit')

# If file was uploaded to Amazon RDS SQL, then allow for SQL queries through pandas
conn = create_engine(os.environ.get("SQL_CONNECTION_STRING")).connect()
if st.session_state['sql']:
    query = st.text_input("Please enter a properly formatted SQL query")
    if st.button("Submit Query"):
        st.dataframe(pd.read_sql(query, conn))
    if st.button("Done querying", type='primary'):
        st.session_state['sql'] = False

