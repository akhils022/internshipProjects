"""
Tools for SQL queries.
"""

import pandas as pd
from google.cloud.sql.connector import Connector
import sqlalchemy
from decimal import Decimal
import os

# Set up SQL connection
connector = Connector()
engine = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=lambda: connector.connect(
        os.environ.get("DB_STRING"),
        "pymysql",
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        db=os.environ.get("DB_NAME"),
    ),
)

# Helper function to convert DECIMAL entries to float
def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    return obj

def sql_query(
    query: str,
) -> dict:
  
    """
    Query an SQL database with the provided string and return relevant results.

    Args:
        query (str): The SQL query in string format to use

    Returns:
        dict: The status and query results
    """    

    try:
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(query)).fetchall()
            result_list = [row._asdict() for row in result]
            result_list = [convert_decimal(row) for row in result_list]
            return {
                "status": "success",
                "message": f"Succefully queried {query} to database",
                "result": result_list,
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error querying database: {str(e)}",
            "result": "",
        }

def table_structure(
    table: str,
) -> dict:
  
    """
    Queries for the table schema for syntax reference.

    Args:
        table (str): The table name to query from

    Returns:
        dict: The status and results from query
    """    

    try:
        table_obj = sqlalchemy.Table(table, sqlalchemy.MetaData(), autoload_with=engine)
        result = [{"name": column.name, "type": str(column.type)} for column in table_obj.columns]
        return {
            "status": "success",
            "message": f"Succesfully got table structure",
            "result": result,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error querying database: {str(e)}",
            "result": "",
        }

def add_table(
    url : str,
    table : str,
) -> dict:
  
    """
    Add a CSV google drive link to the database, under the table with provided name

    Args:
        url (str): The Google Drive link to the CSV file
        table (str): The name of the table to store the data under

    Returns:
        dict: The status and operation results
    """    

    try:
        file_id = url.split('/')[-2]
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        df = pd.read_csv(download_url)
        df.to_sql(table, engine, if_exists='append', index=False)

        return {
            "status": "success",
            "message": f"Succefully created {table} table",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating table: {str(e)}",
        }
    
def delete_table(
    table : str,
) -> dict:
  
    """
    Deletes a specified table from the database

    Args:
        table (str): The name of the table to delete

    Returns:
        dict: The status and operation results
    """    

    try:
        if table in sqlalchemy.inspect(engine).get_table_names():
            table_obj = sqlalchemy.Table(table, sqlalchemy.MetaData(), autoload_with=engine)
            table_obj.drop(engine)
            return {
                "status": "success",
                "message": f"Succefully deleted {table} table",
            }
        else:
            return {
                "status": "error",
                "message": f"Error deleting table: Table does not exist",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error deleting table: {str(e)}",
        }
    
def list_tables() -> dict:
  
    """
    Lists all tables in database

    Args:
        None

    Returns:
        dict: The status and operation results
    """    

    try:
        tables = sqlalchemy.inspect(engine).get_table_names()
        return {
            "status": "success",
            "message": f"Succefully listed tables",
            "tables": tables
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing table: {str(e)}",
        }
    