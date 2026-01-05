from fastapi import Header,HTTPException
import redis
import json
import sqlite3
import time
# redis_client = redis.Redis(
#     host="redis",
#     port=6379,
#     decode_responses=True
# )
# def get_sf_session(session_id:str)->dict:
#     key = f"sf_session:{session_id}"
#     data = redis_client.get(key)
#     if not data:
#         return None
#     return json.loads(data)
DB_PATH = "/Users/vigneshsharma/Desktop/Langgraph/pod_containers/storage_db.db"

def get_sf_session(session_id: str) -> dict | None:
    try:
        print("Inside GET SF session")

        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT account, host, token, token_issued_at, expires_at
            FROM sf_sessions
            WHERE session_id = ?
            """,
            (session_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return dict(row)  

    except Exception as e:
        print(f"Raised Exception in get SF session : {str(e)}")
        return None

def resolve_sf_session(x_session_id:str=Header(...)):
    try:
        print("Received X-Session-Id:", x_session_id)
        session = get_sf_session(x_session_id)
        if not session:
            raise HTTPException(
                status_code = 401,
                detail = "Invalid or expired snowflake session."
            )

        return session
    except Exception as e:
        print(f"Raised error in Reslove SF Session Dependency : {str(e)}")