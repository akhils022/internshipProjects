import os
import streamlit as st
import pandas as pd
import boto3
import requests
import time

# Helper function that uploads to S3 bucket
def uploadToS3(file, key):
    s3 = boto3.client('s3',
                  region_name='ap-south-1',
                  aws_access_key_id=os.environ.get("ACCESS_KEY"),
                  aws_secret_access_key=os.environ.get("SECRET_ACCESS_KEY"))
    try:
        s3.upload_fileobj(file, 'streamlits3test', key)
        st.success("File uploaded to S3")
    except:
        st.error('Unable to upload file to S3')

# Helper function that grabs metadata for file and adds to dataframe
def addMetadata(key):
    param = {'key': key}
    response = requests.get('https://kf1rc3vyx3.execute-api.ap-south-1.amazonaws.com/test/getfile', params=param)
    data = response.json()
    st.session_state['df'].loc[st.session_state['df'].shape[0]] = [data.get('key'), 
                                data.get('size'), data.get('date'), data.get('time')]

# Title
st.title('Welcome to a S3 file upload interface:')
st.header("Please upload a file to store in S3:")

file = st.file_uploader(label='Upload File')

if 'df' not in st.session_state:
    st.session_state['df'] = pd.DataFrame([], columns=["File Key", "Size (bytes)", "Last Modified Date", "Last Modified Time (UTC)"])

# If file uploaded, ask for key
if file is not None:
    n = st.text_input("Enter S3 Key (case insensitive)", file.name)
    # Once key confirmed, upload and add metadata to table
    if (st.button('Submit')):
        key = n.title().lower()
        k = st.success(key)
        uploadToS3(file, key)
        time.sleep(2)
        k.empty()
        addMetadata(key)
    else:
        st.warning('Please enter a key for S3 object')    
else:
    st.warning('Please upload a file to upload')

# Display uploaded file metadata
st.header("Uploaded Files:")
st.table(st.session_state['df'])
