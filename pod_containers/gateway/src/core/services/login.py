from fastapi import APIRouter
from core.services.session import create_session
import snowflake.connector
import time
import json,os,jwt
import base64
import hashlib
import uuid
from dotenv import load_dotenv
from pydantic import BaseModel
from core.utils.config import PUBLIC_KEY_PATH,PRIVATE_KEY_PASSPHRASE,PRIVATE_KEY_PATH,CORTEX_ENDPOINT,USER
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key

load_dotenv()

router = APIRouter()



class QueryPayload(BaseModel):
    user : str
    password : str

@router.post("/login")
def login(payload:QueryPayload):
    try:
        passphrase = PRIVATE_KEY_PASSPHRASE
        session_id = str(uuid.uuid4())
        sf_session = create_snowflake_session(
            public_key_path=PUBLIC_KEY_PATH,
            private_key_path= PRIVATE_KEY_PATH,
            account=os.getenv("SF_ACCOUNT"),
            user=payload.user,
            passphrase = passphrase
        ) 
        print("Session Information ",sf_session)
        login_status = create_session(session_id,sf_session)
        if login_status:    
            return {
                "session_id":session_id,
                "expires_in":'3600',
                "status":"logged in"}

    except Exception as e:
        print(f"Got Error in login API :{str(e)} ")
        return {"status":"login failed"}


def compute_public_key_fingerprint(public_key_path:str)->str:
    """
    Compute SHA256 fingerprint of the public key in the same way Snowflake examples do:
    (DER-encode the public key -> sha256 -> base64), then prefix with 'SHA256:'.
    """
    with open(public_key_path,"rb") as f:
        pub_pem = f.read()
    pub = load_pem_public_key(pub_pem)
    der = pub.public_bytes(
        encoding = serialization.Encoding.DER,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )
    sha = hashlib.sha256(der).digest()
    b64 = base64.b64encode(sha).decode("utf-8")
    return f"SHA256:{b64}"

def create_snowflake_session(private_key_path:str,public_key_path:str,account:str,user:str,passphrase:bytes|None,expiry_seconds:int=3600)->str:
    """
    Build JWT with required Snowflake fields and sign with RSA private key (RS256).
    """

    #fingerprint
    fingerprint = compute_public_key_fingerprint(public_key_path)

    acc = account.upper()
    usr = user.upper()

    # iss : ACCOUNT.USER.SHA256<fingerprint-without-SHA256:?>
    iss = f"{acc}.{usr}.{fingerprint}"
    sub = f"{acc}.{usr}"

    now = int(time.time())

    payload = {
        "iss":iss,
        "sub":sub,
        "aud":"snowflake",
        "iat":now,
        "exp":now+expiry_seconds
    }

    with open(private_key_path,'rb') as f:
        priv_pem = f.read()
    
    # If the key is encrypted use cryptography to decrypt and pass the key object to pyjwt
    if passphrase:
        priv_key_obj = load_pem_private_key(priv_pem,password=passphrase)
        token = jwt.encode(payload,priv_key_obj,algorithm="RS256")
    else:
        token = jwt.encode(payload,priv_pem,algorithm="RS256")
    
    if isinstance(token,bytes):
        token = token.decode("utf-8")
    
    return {
        "account":account,
        "host":f"{account}.snowflakecomputing.com",
        "token":token,
        "token_issued_at":time.time()
    } 

    # conn = snowflake.connector.connect(
    #     account = account,
    #     user=user,
    #     password=password,
    #     warehouse=warehouse,
    #     role = role,
    #     client_session_keep_alive = True
    # )
    # rest = conn.rest
    # return {
    #     "account":account,
    #     "host":f"{account}.snowflakecomputing.com",
    #     "token":rest.token,
    #     "token_issued_at":time.time(),
    #     "conn":conn # kept for refresh
    # }
