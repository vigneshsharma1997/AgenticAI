from typing import TypeDict, List , Any

class ChatState(TypeDict):
    history : List[dict]
    question:str