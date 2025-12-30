from fastapi import APIRouter,Depends,HTTPException,status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import httpx


class ChatRequest(BaseModel):
    user_id:str
    session_id:str
    user_query:str


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]  
)

@router.post("/messages")
async def process_user_request(chat_request:ChatRequest):
    print("Processing User request")
    async with httpx.AsyncClient() as client:
        try :
            response = await client.post(f"{os.getenv('TEXT_TO_SQL_URL','http://localhost:8001')}/chat_graph",
                json = chat_request.dict(),
                timeout=120)
            response.raise_for_status()
            task_response=response.json()
            print("User Request processed succesfully.")
            return {'response':task_response}
        except Exception as e:
            print(f"Error occured in process query gateway : {str(e)}")
            return {"error":str(e)}