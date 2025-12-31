from typing import TypedDict, List, Any

class ChatState(TypedDict):
    history : List[dict]
    question:str