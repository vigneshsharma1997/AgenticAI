from langgraph.graph import StateGraph , START,END
from core.services.chat import chat_node
from core.services.state import ChatState

async def build_graph():
    builder = StateGraph(ChatState)
    builder.add_node("chat",chat_node)
    builder.set_entry_point("chat")
    builder.add_edge(START,"chat")
    builder.add_edge("chat",END)
    graph = builder.compile()
    return graph
    