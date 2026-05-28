"""
LangGraph Graph Definition — Financial Agent StateGraph
"""
from langgraph.graph import StateGraph, END
from state import AgentState
from memory import checkpointer
from nodes import (
    retrieve_documents,
    grade_documents,
    rewrite_query,
    search_web,
    compress_documents,
    assess_need_sql,
    query_sql,
    generate_answer,
    route_after_grade,
    route_after_assess,
)


def build_graph():
    """Build and compile the LangGraph financial agent."""
    workflow = StateGraph(AgentState)

    # ── Add nodes ──
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("grade", grade_documents)
    workflow.add_node("compress", compress_documents)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("search_web", search_web)
    workflow.add_node("assess", assess_need_sql)
    workflow.add_node("query_sql", query_sql)
    workflow.add_node("generate", generate_answer)

    # ── Entry point ──
    workflow.set_entry_point("retrieve")

    # ── Edges ──
    workflow.add_edge("retrieve", "grade")

    # After grading: relevant → compress | not relevant → rewrite (max 1 retry) | or fallback to web
    workflow.add_conditional_edges(
        "grade",
        route_after_grade,
        {
            "compress": "compress",
            "rewrite": "rewrite",
            "search_web": "search_web",
        }
    )
    
    # Rewrite -> retrieve to try RAG again
    workflow.add_edge("rewrite", "retrieve")

    # Search web fallback -> assess directly
    workflow.add_edge("search_web", "assess")
    
    workflow.add_edge("compress", "assess")

    # After assess: need SQL → query_sql | enough → generate
    workflow.add_conditional_edges(
        "assess",
        route_after_assess,
        {
            "query_sql": "query_sql",
            "generate": "generate",
        }
    )

    # SQL → Generate → END
    workflow.add_edge("query_sql", "generate")
    workflow.add_edge("generate", END)

    # ── Compile with memory checkpointer ──
    graph = workflow.compile(checkpointer=checkpointer)
    print("[GRAPH] LangGraph Financial Agent compiled successfully")
    return graph


# Singleton graph instance
graph = build_graph()
