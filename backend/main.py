"""
FastAPI Application — DJIA Financial Agent with LangGraph
"""
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from graph import graph
from memory import get_thread_config

app = FastAPI(title="DJIA Financial Agent — LangGraph")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ──

class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    route: str = "langgraph"
    sql_query: str | None = None
    sources: list[str] = []


class SessionResponse(BaseModel):
    session_id: str


# ── Endpoints ──

@app.get("/")
def root():
    return {"message": "DJIA Financial Agent (LangGraph) is running 🚀"}


@app.post("/session/new", response_model=SessionResponse)
def new_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    return SessionResponse(session_id=session_id)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a message to the financial agent."""
    session_id = req.session_id or str(uuid.uuid4())
    config = get_thread_config(session_id)

    # Invoke graph
    result = graph.invoke(
        {
            "question": req.question,
            "messages": [HumanMessage(content=req.question)],
            "documents": [],
            "web_results": "",
            "sql_result": "",
            "sql_query": "",
            "generation": "",
            "retry_count": 0,
        },
        config,
    )

    # Build sources list
    sources = []
    docs = result.get("documents", [])
    if docs:
        for d in docs[:3]:
            sources.append(f"[DOC] {d['company']} - {d['section']}")
    if result.get("sql_result") and "Error" not in result.get("sql_result", ""):
        sources.append("[SQL] Database")
    if result.get("web_results") and "Lỗi" not in result.get("web_results", ""):
        sources.append("[WEB] Web Search")

    return ChatResponse(
        answer=result.get("generation", "Không có câu trả lời."),
        session_id=session_id,
        sql_query=result.get("sql_query"),
        sources=sources,
    )


@app.get("/session/{session_id}/history")
def get_history(session_id: str):
    """Get chat history for a session."""
    config = get_thread_config(session_id)
    try:
        state = graph.get_state(config)
        messages = state.values.get("messages", [])
        history = []
        for m in messages:
            history.append({
                "role": "user" if m.type == "human" else "agent",
                "content": m.content,
            })
        return {"session_id": session_id, "history": history}
    except Exception:
        return {"session_id": session_id, "history": []}


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """Delete a chat session (clear memory)."""
    # MemorySaver doesn't support deletion natively,
    # but the session will no longer be used.
    return {"message": f"Session {session_id} marked for deletion"}
