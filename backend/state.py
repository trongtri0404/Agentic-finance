"""
LangGraph Agent State Definition
"""
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State schema for the financial agent graph."""
    question: str                                           # Current user question
    documents: list[dict]                                   # Retrieved RAG documents
    compressed_documents: list[dict]                        # Documents after Context Compression
    web_results: str                                        # Tavily web search results
    sql_result: str                                         # SQL query result
    sql_query: str                                          # Generated SQL query
    generation: str                                         # Final generated answer
    retry_count: int                                        # Retry counter for rewrite loop
    messages: Annotated[Sequence[BaseMessage], add_messages] # Chat history (memory)
