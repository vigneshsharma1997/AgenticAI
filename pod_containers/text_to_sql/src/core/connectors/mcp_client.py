from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools import Tool
import asyncio
import os
import json
from dotenv import load_dotenv
load_dotenv()

async def get_mcp_tool():
    try:
        client = MultiServerMCPClient({
            "MCP_Server":{
                "url":os.getenv("MCP_URL"),
                "transport" : "streamable_http"
            }
        })
        tools = await client.get_tools()
        print("Successfully retrieved MCP Tools.")
        return tools
    except Exception as e:
        print(f"Error in MCP client : {e}")

async def async_sql_query(query:str):
    tools = await get_mcp_tool()
    sql_tool = next((t for t in tools if t.name.lower() == "run_sql"), None)
    if not sql_tool:
                return json.dumps({"error": "No SQL tool 'run_sql' found on MCP server"})
    return await sql_tool.ainvoke({"query":query})


sql_query_tool = Tool(
      name = "sql_query",
      description = "Execute SQL queries via MCP server using 'run_sql' (async only)",
      func = async_sql_query
)

async def create_mcp_sql_query_tool(sql_query_tool):

    async def async_resolve(query: str):
        raw_result = await sql_query_tool.func(query)  # returns JSON string from DB
        try:
            parsed_result = json.loads(raw_result)  # parse JSON string
        except Exception:
            parsed_result = {"columns": [], "rows": []}
        return parsed_result

    def sync_resolve(input_json:str):
         try:
              inp= json.loads(input_json)
              query = inp.get("query")
              if not query:
                   return json.dumps({"columns":[],"rows":[]})
              try:
                   loop = asyncio.get_running_loop()
                   future = asyncio.run_coroutine_threadsafe(async_resolve(query),loop)
                   reslt = future.result()
              except RuntimeError:
                   result = asyncio.run(async_resolve(query))
         
              return json.dumps(result)
         except Exception as e:
            return json.dumps({
                "columns": [],
                "rows": [],
                "error": str(e)
            })
    return Tool(
        name="mcp_sql_query",
        description="Sql tool that queries SQLite datasets based on user inputs",
        func=sync_resolve
    )