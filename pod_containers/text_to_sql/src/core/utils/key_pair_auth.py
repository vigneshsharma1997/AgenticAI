import time
import base64
import hashlib
import json
import requests
import os
import jwt  # PyJWT
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key
from dotenv import load_dotenv
load_dotenv()
# ---------- CONFIG ----------
ACCOUNT_IDENTIFIER = "CGVJNYQ-PCA73931"   # use exact account identifier / locator (UPPERCASE)
USER = "VIGNESH10"                        # your snowflake username (UPPERCASE)
PRIVATE_KEY_PATH = os.path.expanduser("/Users/vigneshsharma/rsa_key.pem")   # path to your private key (change)
PUBLIC_KEY_PATH = os.path.expanduser("/Users/vigneshsharma/rsa_key.pub")   # path to public key (change)
PRIVATE_KEY_PASSPHRASE = None   # if your private key is encrypted: b"your-passphrase"
# Cortex endpoint (example)
# CORTEX_ENDPOINT = f"https://{ACCOUNT_IDENTIFIER.lower()}.snowflakecomputing.com/api/v2/cortex/analyst/message"
CORTEX_ENDPOINT = f"https://{ACCOUNT_IDENTIFIER.lower()}.snowflakecomputing.com/api/v2/databases/{os.getenv('SF_DATABASE')}/schemas/{os.getenv('SF_SCHEMA')}/agents/{os.getenv('SF_AGENT')}:run"

# --------------------------------

def compute_public_key_fingerprint(public_key_path: str) -> str:
    """
    Compute SHA256 fingerprint of the public key in the same way Snowflake examples do:
    (DER-encode the public key -> sha256 -> base64), then prefix with 'SHA256:'.
    """
    with open(public_key_path, "rb") as f:
        pub_pem = f.read()

    pub = load_pem_public_key(pub_pem)
    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    sha = hashlib.sha256(der).digest()
    b64 = base64.b64encode(sha).decode("utf-8")
    # Snowflake shows the fingerprint as 'SHA256:<base64string>' (often with padding "=").
    return f"SHA256:{b64}"

def generate_keypair_jwt(private_key_path: str, public_key_path: str,
                         account: str, user: str,
                         passphrase: bytes | None = None,
                         expiry_seconds: int = 3600) -> str:
    """
    Build JWT with required Snowflake fields and sign with RSA private key (RS256).
    """
    # fingerprint
    fingerprint = compute_public_key_fingerprint(public_key_path)

    # Build claims: account and user must be uppercase
    acc = account.upper()
    usr = user.upper()

    # iss must be: ACCOUNT.USER.SHA256:<fingerprint-without-SHA256:?> but docs require prefix 'SHA256:' kept
    iss = f"{acc}.{usr}.{fingerprint}"
    sub = f"{acc}.{usr}"

    now = int(time.time())
    payload = {
        "iss": iss,
        "sub": sub,
        "aud": "snowflake",
        "iat": now,
        "exp": now + expiry_seconds
    }

    # load private key (supports encrypted private key when passphrase provided)
    with open(private_key_path, "rb") as f:
        priv_pem = f.read()

    # If the key is encrypted, use cryptography to decrypt and pass the key object to pyjwt
    if passphrase:
        private_key_obj = load_pem_private_key(priv_pem, password=passphrase)
        token = jwt.encode(payload, private_key_obj, algorithm="RS256")
    else:
        # pass raw PEM bytes (pyjwt accepts PEM)
        token = jwt.encode(payload, priv_pem, algorithm="RS256")

    # PyJWT >= 2 returns str
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def call_cortex(jwt_token: str, question: str):
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT",  # explicit
    }

    body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    { "type": "text", "text": question }
                ]
            }
        ],
        # use your semantic view or model reference if you have one; otherwise remove
        "semantic_model_file": "@CORTEX_ANALYST_DEMO.REVENUE_TIMESERIES.RAW_DATA/revenue_timeseries.yaml"
    }

    resp = requests.post(CORTEX_ENDPOINT, json=body, headers=headers, timeout=30)
    print("status:", resp.status_code)
    print("response:", resp.text)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    # quick sanity checks
    assert os.path.exists(PRIVATE_KEY_PATH), f"Private key not found: {PRIVATE_KEY_PATH}"
    assert os.path.exists(PUBLIC_KEY_PATH), f"Public key not found: {PUBLIC_KEY_PATH}"

    print("Public key fingerprint:", compute_public_key_fingerprint(PUBLIC_KEY_PATH))
    jwt_token = generate_keypair_jwt(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH, ACCOUNT_IDENTIFIER, USER, PRIVATE_KEY_PASSPHRASE)
    print("JWT length:", len(jwt_token))
    # optional: print first 200 chars (do NOT log private tokens in prod)
    print(jwt_token[:200], "...")

    # Call Cortex (example question)
    try:
        result = call_cortex(jwt_token, "How many distinct product lines are present?.")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("Call failed:", e)
