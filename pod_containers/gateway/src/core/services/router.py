from fastapi import APIRouter,Depends,HTTPException,status,Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import httpx
TOKEN_REFRESH_BUFFER = 60  # seconds

class ChatRequest(BaseModel):
    user_id:str
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
        
# @router.post("/chat")
# async def proxy_chat(
#     payload: dict,
#     x_session_id: str = Header(...),
# ):
#     try:
#         sf_session = get_or_refresh_sf_session(x_session_id)
#     except ValueError:
#         raise HTTPException(status_code=401, detail="Invalid session")

#     # Forward request to chat service
#     # return forward_to_chat_service(payload, x_session_id)
#     print("Processing User request")
#     async with httpx.AsyncClient() as client:
#         try :
#             response = await client.post(f"{os.getenv('TEXT_TO_SQL_URL','http://localhost:8001')}/sf_chat",
#                 json = payload.dict(),
#                 timeout=120)
#             response.raise_for_status()
#             task_response=response.json()
#             print("User Request processed succesfully.")

#             return {'response':task_response}
#         except Exception as e:
#             print(f"Error occured in process query gateway : {str(e)}")
#             return {"error":str(e)}
        

# def get_or_refresh_sf_session(session_id):
    
#     session = load_sf_session(session_id)

#     if not session:
#         raise ValueError("Session not found")

#     now = time.time()

#     # 🔁 Refresh if token is close to expiry
#     if session["expires_at"] - now < TOKEN_REFRESH_BUFFER:
#         session = refresh_sf_token(session_id, session)

#     return session


# def load_sf_session(session_id):
#     pass