import asyncio
from core.services.agent import run_agent
from core.services.state import ChatState


async def chat_node(state:ChatState)->ChatState:
    """
    Node Function that call our chat agent async and return state updates.
    - 'State': is current state of the object.
    - 'Inputs': is a dict for any external inputs (new_question).
    Returns a dict state updates.
    """
    question = state.get("question")
    history = state.get("history")
    if question is None:
        return {"history":[],"question":"No question provided"}
    try : 
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(run_agent(question,history))
    except Exception as e:
        result = asyncio.run(run_agent(question,history))
    
    new_history_entry = {"question":question,"answer":result}
    return {"history":state["history"]+[new_history_entry], "question":question}