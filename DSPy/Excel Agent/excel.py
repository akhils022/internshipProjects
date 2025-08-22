"""
Tool for querying Vertex AI RAG corpora and retrieving relevant information.
"""

import os
import pandas as pd
import logging
import json
import sqlite3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def read_file(file_path: str):
    """
    Reads data from an Excel (.xls, .xlsx) or CSV file.

    Args:
        file_path: The path to the file to be read.

    Returns:
        A pandas DataFrame containing the file's data if successful,
        or an error message if the file is not found or the format is unsupported.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at '{file_path}'."

    file_extension = os.path.splitext(file_path)[1].lower()

    try:
        if file_extension in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
            logger.info(f"Successfully read file at {file_path}")
            return {
            "status": "success",
            "message": f"Successfully read file at {file_path}",
            "contents": df.to_json(),
            }
        elif file_extension == '.csv':
            df = pd.read_csv(file_path)
            logger.info(f"Successfully read file at {file_path}")
            return {
            "status": "success",
            "message": f"Successfully read file at {file_path}",
            "contents": df.to_json(),
            }
        else:
            logger.error(f"Error: Unsupported file type '{file_extension}'. Please provide an Excel or CSV file.")
            return {
            "status": "error",
            "message": f"Error: Unsupported file type '{file_extension}'. Please provide an Excel or CSV file.",
            }
    except Exception as e:
        logger.error(f"An error occurred while reading the file: {e}")
        return {
            "status": "error",
            "message": f"An error occurred while reading the file: {e}",
            }

def write_file(file_content : str):
    """
    Writes JSON formatted data to an Excel file to be downloaded.

    Args:
        file_content: The JSON formatted Excel file to be written.

    Returns:
        A success or error message depending on the result of the operation.
    """

    try:
        data = json.loads(file_content.strip("```json").strip("```").strip())
        new_df = pd.DataFrame(data)

        file_path = "output.xlsx"

        if os.path.exists(file_path):
            # Load existing data
            existing_df = pd.read_excel(file_path)
            # Append new data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            # No existing file, just use new data
            combined_df = new_df


        combined_df.to_excel("output.xlsx", index=False)
        logger.info("Successfully wrote output excel file")
        return {
                "status": "success",
                "message": "Successfully wrote output excel file",
            }
    except Exception as e:
        logger.error(f"An error occurred while writing to excel file: {e}")
        return {
            "status": "error",
            "message": f"An error occurred while writing to excel file: {e}",
        }

def write_to_db(file_content : str):
    """
    Writes JSON formatted data to a SQLite DB.

    Args:
        file_content: The JSON formatted Excel file to be written.

    Returns:
        A success or error message depending on the result of the operation.
    """

    try:
        data = json.loads(file_content.strip("```json").strip("```").strip())
        df = pd.DataFrame(data)
        expected_cols = {'Organization', 'Website', 'Employee', 'Contact', 'Designation', 'Email', 'Mobile', 'Telephone',
                         'Address', 'City', 'State', 'Country', 'Industry', 'Other'}
        if not expected_cols.issubset(df.columns):
            raise ValueError("Missing expected columns.")

        with sqlite3.connect("temp.db") as conn:
            df.to_sql('data_table', conn, if_exists='append', index=False)
            logger.info("Successfully wrote to db")
            return {
                "status": "success",
                "message": "Successfully wrote to db",
            }
    except Exception as e:
        logger.error(f"An error occurred while writing to db: {e}")
        return {
            "status": "error",
            "message": f"An error occurred while writing to db: {e}",
        }