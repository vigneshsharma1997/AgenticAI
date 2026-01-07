import os
from dotenv import load_dotenv
load_dotenv()

ACCOUNT_IDENTIFIER = os.getenv("SF_ACCOUNT")
USER = os.getenv("SF_USER")
ALLOWED_ORIGINS = ["*"]
TRUSTED_DOMAINS = []
PRIVATE_KEY_PASSPHRASE = None
PRIVATE_KEY_PATH = os.path.expanduser("/Users/vigneshsharma/rsa_key.pem")   # path 
PUBLIC_KEY_PATH = os.path.expanduser("/Users/vigneshsharma/rsa_key.pub") 

CORTEX_ENDPOINT = f"https://{ACCOUNT_IDENTIFIER.lower()}.snowflakecomputing.com/api/v2/cortex/analyst/message"