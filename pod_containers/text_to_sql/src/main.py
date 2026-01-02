from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import os
from dotenv import load_dotenv
import json
from core.connectors.mcp_client import get_mcp_tool
from core.services.state import ChatState
from core.services.graph import build_graph
from typing import TypedDict, List , Any
from langchain_core.runnables.config import RunnableConfig

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = False,
    allow_methods = ["GET","POST","OPTIONS"],
    allow_headers = ["*"]
)

class QueryPayload(BaseModel):
    user_id : str
    session_id : str
    user_query : str
    # chathistory : List[dict]


@app.post("/chat_graph")
async def chat_graph_node(req:QueryPayload):
    graph = await build_graph()
    # history = req.chathistory
    history = []
    initial_state: ChatState = {"history":history,"question":req.user_query}
    final_state = initial_state
    config = RunnableConfig(configurable = {'session_id':req.session_id})
    
    async for event in graph.astream(initial_state,config=config):
        final_state = event['chat']
    
    print("All events complete")
    # last_entry = final_state['history'][-1] if final_state['history'] else None
    # if last_entry and "output" in last_entry:
    #     return {"question":req.user_query,"answer":last_entry["output"]}
    # if last_entry and "answer" in last_entry:
    #     possible_answer = last_entry["answer"]
    #     try:
    #         if isinstance(possible_answer,str):
    #             # Answer is Just a string
    #             return {"question":req.user_query,"answer": possible_answer}
            
    #         if possible_answer and "output" in possible_answer:
    #             output = possible_answer['output']
    #             if isinstance(output,str):
    #                 try:
    #                     json_answer = json.loads(output)
    #                     if json_answer:
    #                         return {"question":req.user_query,"answer":json_answer}
    #                 except Exception as e:
    #                     print(f" Error in Generating Response possible answer : {e}")
    #     except Exception as e:
    #         print(f"Error in possible answer : {e}")

    # answer = json.loads(last_entry['answer']['output']) if last_entry else None
    # return {"question":"answer",
    #         "answer":answer}

    # SAFELY extract answer from final_state
    answer = final_state.get("answer")

    # If agent returned JSON string → parse it
    if isinstance(answer, str):
        try:
            parsed = json.loads(answer)
            answer = parsed
        except Exception:
            pass  # keep original string

    return {
        "question": req.user_query,
        "answer": answer
    }


if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0",port = 8001, reload=True)