## This is a Agentic AI Snowflake cortex Codebase handling Analytical Queries. ##

Step 1: Create dot env with following variables.
SF_ACCOUNT = ""
SF_ROLE = ""
SF_WAREHOUSE = ""
SF_USER = ""
SF_DATABASE = "<none selected>"
SF_SCHEMA = "<none selected>" 

Step 2 : Run Gateway /login API 
Command : uvicorn main:app --reload --host 0.0.0.0 --port 8000
Payload : user: USERID
          assword : PASSWORD
This will create a session in storage_db. Copy session_id.

Step 3 : run text_to_sql /sf_chat API
Command : uvicorn main:app --reload --host 0.0.0.0 --port 8001
Use Session id from storage_db.
Payload :
        Enter : <session_id>
        {
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "what is total revenue for each product id?"
        }
        ]
        }
    ],
      "semantic_model_file": "@CORTEX_ANALYST_DEMO.REVENUE_TIMESERIES.RAW_DATA/revenue_timeseries.yaml",
      "streaming": false
    }