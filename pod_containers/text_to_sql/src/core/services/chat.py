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
    try:
        print("In Chat Node")
        result = await run_agent(question, history)
    except Exception as e:
        return {
            "history": history,
            "answer": f"Agent execution failed: {str(e)}"
        }

    new_history_entry = {"question":question,"answer":result}
    return {"history":state["history"]+[new_history_entry], "question":question}