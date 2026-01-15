import requests
from typing import Dict,Generator,Optional,AsyncGenerator
from fastapi import HTTPException
from dotenv import load_dotenv
import os
import httpx
from fastapi.encoders import jsonable_encoder
import json

load_dotenv()

class SnowflakeCortexConnector:
    """
    Generic Snowflake REST connector.
    Designed to be reused across Analyst, Search, Agents.
    """
    def __init__(self,
        account_host:str,
        token:str,
        timeout:60):
        self.host_url = f"https://{account_host}/"
        self.timeout= timeout
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT"
        }

        # self.headers = {
        #     "Content-Type":"application/json",
        #     "Authorization":f"Snowflake Token : {self.token} "
        # }

    # def post(self,endpoint_url:str,payload:Dict,stream:bool=False) -> requests.Response:
    #     url = f"{self.host_url}{endpoint_url}"
    #     response = requests.post(
    #         url = url,
    #         json = payload,
    #         headers= self.headers,
    #         timeout= self.timeout,
    #         stream=stream
    #     )
    #     response.raise_for_status()
    #     return response

    def post(self, endpoint_url: str, payload: dict, stream: bool = False) -> requests.Response:
        url = f"{self.host_url}{endpoint_url}"
        response = requests.post(
            url=url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )
        # Do NOT raise without logging the body first
        if not response.ok:
            # Log diagnostic info
            print("CORTEX POST URL:", url)
            print("REQUEST HEADERS:", self.headers)
            print("STATUS:", response.status_code)
            print("RESPONSE TEXT:", response.text)
            # Return or raise a friendly error
            raise HTTPException(status_code=502, detail=f"Cortex error {response.status_code}: {response.text}")
        
        response.raise_for_status()
        return response.json()
    
    def stream_response(self,endpoint:str,payload:Dict)->Generator[str,None,None]:
        """
            Stream Cortex responses line by line (SSE style)
        """
        url = f"{self.host_url}{endpoint}"
        response = requests.post(
            url = url,
            json=payload,
            stream=True
        )
        for line in response.iter_lines(decode_unicode=True):
            if line:
                yield line

    async def create_thread_id(self,token,origin_app)->str:
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        payload = {"origin_application": origin_app} if origin_app else {}
        endpoint = "/api/v2/cortex/threads"
        url = f"{self.host_url}{endpoint}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200 and resp.status_code != 201:
                raise HTTPException(status_code=502, detail=f"Failed to create thread: {resp.status_code} {resp.text}")
            return resp.text.strip('"')
    

    async def stream_run_agent(self,token,req)->AsyncGenerator[bytes,None]:
        """
            Calls agent run and yields server-sent events (SSE) bytes as they arrive.
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        }

        request = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "what is total revenue for each product id?"}
                        ],
                    }
                ]
            }
            
        AGENT_RUN_ENDPOINT_TEMPLATE = f"{self.host_url}api/v2/databases/{os.getenv('SF_DATABASE')}/schemas/{os.getenv('SF_SCHEMA')}/agents/{os.getenv('SF_AGENT')}:run"

        print(f"===Cortex Agent URL : {AGENT_RUN_ENDPOINT_TEMPLATE}")
        print(f"Request Payload: {request}")
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                AGENT_RUN_ENDPOINT_TEMPLATE,
                headers=headers,
                json=request,
            ) as resp:

                if resp.status_code != 200:
                    error = await resp.aread()
                    raise HTTPException(
                        status_code=502,
                        detail=f"agent:run failed: {resp.status_code} {error.decode()}",
                    )

                async for chunk in resp.aiter_bytes():
                    yield chunk