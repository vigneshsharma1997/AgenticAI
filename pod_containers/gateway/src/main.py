from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
# from core.session
from core.utils.config import ALLOWED_ORIGINS, TRUSTED_DOMAINS
from core.services import router,session,login

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods = ['GET','POST','OPTIONS','DELETE'],
    allow_headers = ['*']
)
# app.add_middleware(TrustedHostMiddleware,allowed_hosts = TRUSTED_DOMAINS)
# app.add_middleware(SessionMiddleware)

API_PREFIX = "/api/v1"
app.include_router(login.router)
app.include_router(router.router, prefix = API_PREFIX)

@app.get("/get_health_check",tags=["Health Check"])
async def health_check():
    "Health Check endpoint to ensure API service is running properly"
    return {"message":"Welcome to Gateway Service health check endpoint."}

# uvicorn main:app --reload --host 0.0.0.0 --port 8000
