import streamlit as st
from agent import analytical_agent_dspy
import sqlite3
import pandas as pd
import dspy
import os

if not "temp" not in st.session_state:
    dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash", api_key=os.environ.get("GOOGLE_API_KEY"),
                              max_tokens=100000))
    st.session_state['temp'] = True

st.title("Excel File Extraction Agent")

def process_chunk(chunk_df, chunk_index):
    chunk_str = chunk_df.to_csv(index=False)
    return analytical_agent_dspy(query=f"Extract information from this data:\n{chunk_str}")

# Streamlit UI
file = st.file_uploader("Submit file here", type=["xls", "xlsx"])
button = st.button("Submit file")

if file and button:
    try:
        df = pd.read_excel(file)
        st.success("File uploaded and read successfully!")
        st.write(df.head())  # Show preview
        with st.spinner("Reading and chunking the Excel file..."):
            chunk_size = 50
            chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
            st.success(f"Split into {len(chunks)} chunks of 50 rows each.")

        all_results = []
        for idx, chunk in enumerate(chunks):
            with st.spinner(f"Processing chunk {idx+1} of {len(chunks)}..."):
                result = process_chunk(chunk, idx+1)
                all_results.append(f"--- Chunk {idx+1} ---\n{result}\n")

        st.subheader("Extraction Results:")
        st.text("\n".join(all_results))

    except Exception as e:
        st.error(f"Error processing Excel file: {e}")

if st.button("Show results:"):
    with sqlite3.connect("temp.db") as conn:
        table = pd.read_sql("SELECT * FROM data_table;", conn)
        st.dataframe(table, hide_index=True)