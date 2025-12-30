from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def get_mcp_tool():
    try:
        client = MultiServerMCPClient({
            "MCP_Server":{
                "url":f"{os.getenv("MCP_URL")}",
                "transport" : "streamable_http"
            }
        })
        tools = await client.get_tools()
        print("Successfully retrieved MCP Tools.")
        return tools
    except Exception as e:
        print(f"Error in MCP client : {e}")