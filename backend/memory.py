"""
Memory / Checkpointer — Per-session chat memory using LangGraph MemorySaver
"""
from langgraph.checkpoint.memory import MemorySaver

# In-memory checkpointer: mỗi session_id (thread_id) lưu state riêng
checkpointer = MemorySaver()


def get_thread_config(session_id: str) -> dict:
    """Get LangGraph config for a specific chat session."""
    return {"configurable": {"thread_id": session_id}}
