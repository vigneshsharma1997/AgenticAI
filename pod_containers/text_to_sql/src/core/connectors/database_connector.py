import requests
from typing import Dict,Generator,Optional
from fastapi import HTTPException
from dotenv import load_dotenv
import os
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
