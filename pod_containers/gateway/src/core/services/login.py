from fastapi import APIRouter
from core.services.session import create_session
import snowflake.connector
import time
import json,os
import uuid
from dotenv import load_dotenv
from pydantic import BaseModel
load_dotenv()

router = APIRouter()

class QueryPayload(BaseModel):
    user : str
    password : str

@router.post("/login")
def login(payload:QueryPayload):
    try:

        session_id = str(uuid.uuid4())
        sf_session = create_snowflake_session(
            account=os.getenv("SF_ACCOUNT"),
            user=payload.user,
            password=payload.password,
            warehouse=os.getenv("SF_WAREHOUSE"),
            role = os.getenv("SF_ROLE")
        ) 
        print("Session Information ",sf_session)
        login_status = create_session(session_id,sf_session)
        if login_status:    
            return {
                "session_id":session_id,
                "expires_in":'60',
                "status":"logged in"}

    except Exception as e:
        print(f"Got Error in login API :{str(e)} ")
        return {"status":"login failed"}



def create_snowflake_session(account:str,user:str,password:str,warehouse:str,role:str):
    conn = snowflake.connector.connect(
        account = account,
        user=user,
        password=password,
        warehouse=warehouse,
        role = role,
        client_session_keep_alive = True
    )
    rest = conn.rest
    return {
        "account":account,
        "host":f"{account}.snowflakecomputing.com",
        "token":rest.token,
        "token_issued_at":time.time(),
        "conn":conn # kept for refresh
    }
