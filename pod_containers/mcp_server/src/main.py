from dotenv import load_dotenv
import os
from fastmcp import FastMCP
import uvicorn
import sqlite3

mcp = FastMCP("MCP_Server")
DB_PATH = ('retail.db')

def get_conn():
    load_dotenv()
    try :
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"Error connecting to databricks : {e}")

@mcp.tool()
def run_sql(query:str)->dict:
    """
    Execute SQL query on Sqlite Database.
    Supports SELECT and Non Select (With CTE) queries.
    """
    cleaned_query = query.encode('utf-8').decode('unicode_escape') # Converts \n to actual newline
    cleaned_query = cleaned_query.replace('\n',' ').replace('\r',' ').strip().rstrip(';') # rstrip removes char right to semicolon
    conn = get_conn()
    print("Cleaned Query in MCP Server ",cleaned_query)
    curr = conn.cursor()
    try:
        curr.execute(cleaned_query)
        if cleaned_query.strip().lower().startswith("select","with"):
            rows = curr.fetchall()
            cols = [d[0] for d in curr.description]
            return {"columns":cols,"rows":rows}
        else:
            conn.commit()
            return {"status":"success"}
    except Exception as e:
        print(f"Exception occured in MCP Server : {e}")
        return {"status":"fail"}
    
if __name__=="__main__":
    mcp.run(transport="http",host="127.0.0.1",port=8085)