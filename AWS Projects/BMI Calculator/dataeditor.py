import streamlit as st
import pandas as pd

# Title
st.title('Welcome to an online CSV file editor:')
st.header("Please upload a CSV file to edit")

file = st.file_uploader(label='Upload CSV', type='.csv')

# If file is uploaded, create interface
if file is not None:
    st.subheader("Editing " + file.name)
    df = pd.read_csv(file)
    # Allows for data editing
    df_edited = st.data_editor(df, num_rows='dynamic')
    f = df_edited.to_csv()
    n = st.text_input("Enter Your Name", file.name[0:-4] + "_edited.csv")
    # When ready, download edited file
    if (st.button('Submit')):
        name = n.title()
        st.success(name)
        if st.download_button(label='Download Edited CSV', data=f, file_name=name):
            st.success('Edited file downloaded')
    else:
        st.warning('Please enter a file name for the downloaded file')
else:
    st.warning('Please upload a CSV file to edit')



