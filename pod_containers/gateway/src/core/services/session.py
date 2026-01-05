import sqlite3

DB_PATH = "/Users/vigneshsharma/Desktop/Langgraph/pod_containers/storage_db.db"

def create_session(session_id:str,session:dict):
    try:

        conn = sqlite3.connect(DB_PATH,check_same_thread=True)
        cursor = conn.cursor()
        # expires = session['token_issued'] + session['token_ttl']
        cursor.execute(
            """
            INSERT OR REPLACE INTO sf_sessions
            (session_id, account, host, token, token_issued_at,expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                session["account"],
                session["host"],
                session["token"],
                session["token_issued_at"],
                60,
            ),
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Got Error while creating SF session : {str(e)}")
        return False