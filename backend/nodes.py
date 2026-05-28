"""
LangGraph Nodes — All graph node functions for the financial agent
Flow: Question -> Retrieve -> Grade -> Assess -> [Query SQL] -> Generate
                                -> Rewrite -> Search Web -> Grade (loop)
"""
from langchain_core.messages import AIMessage
from llm import get_llm
from tools import search_rag_chunks, execute_sql_query, search_web_tavily, DB_SCHEMA
import nltk

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Initialize compressor once to save time
compressor_model = None


def retrieve_documents(state: dict) -> dict:
    """Node: Retrieve documents from RAG (Supabase rag_chunks)."""
    question = state["question"]
    print(f"\n[NODE] Retrieve Documents: '{question[:60]}...'")

    docs = search_rag_chunks(question, limit=5)
    print(f"[NODE] Found {len(docs)} documents")

    return {"documents": docs, "retry_count": state.get("retry_count", 0)}


def grade_documents(state: dict) -> dict:
    """Node: Grade retrieved documents for relevance using LLM."""
    question = state["question"]
    documents = state.get("documents", [])
    print(f"[NODE] Grade Documents ({len(documents)} docs)")

    if not documents:
        return {"documents": []}

    llm = get_llm(temperature=0.1)
    relevant_docs = []

    for doc in documents:
        prompt = f"""Bạn là chuyên gia đánh giá tài liệu tài chính.

Câu hỏi: {question}
Tài liệu: {doc['text'][:500]}

Tài liệu này có liên quan đến câu hỏi không?
Trả lời ĐÚNG MỘT TỪ: "yes" hoặc "no"."""

        try:
            response = llm.invoke(prompt)
            grade = response.content.strip().lower()
            if "yes" in grade:
                relevant_docs.append(doc)
        except Exception as e:
            print(f"[GRADE] LLM error: {e}")
            # If LLM fails, keep the doc as potentially relevant
            relevant_docs.append(doc)

    print(f"[NODE] Relevant: {len(relevant_docs)}/{len(documents)}")
    return {"documents": relevant_docs}


def compress_documents(state: dict) -> dict:
    """Node: Compress retrieved documents using Cross-Encoder to keep only relevant sentences."""
    question = state["question"]
    documents = state.get("documents", [])
    print(f"[NODE] Compress Documents ({len(documents)} docs)")
    
    if not documents:
        return {"compressed_documents": []}
        
    global compressor_model
    if compressor_model is None and CrossEncoder is not None:
        try:
            print("[NODE] Loading Cross-Encoder model...")
            compressor_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        except Exception as e:
            print(f"[COMPRESS] Error loading model: {e}")
            return {"compressed_documents": documents}
            
    if compressor_model is None:
        print("[COMPRESS] CrossEncoder not available, skipping compression.")
        return {"compressed_documents": documents}
            
    # Compress per document to keep company/section structure
    compressed_docs = []
    for doc in documents:
        text = doc['text']
        sentences = nltk.sent_tokenize(text)
        if not sentences:
            continue
            
        model_inputs = [[question, sent] for sent in sentences]
        try:
            scores = compressor_model.predict(model_inputs)
        except Exception as e:
            print(f"[COMPRESS] Inference error: {e}")
            compressed_docs.append(doc)
            continue
            
        scored_sentences = list(zip(scores, sentences))
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Keep top 3 sentences with positive score
        selected = [sent for score, sent in scored_sentences if score > 0.0][:3]
        
        if not selected:
            # Fallback to top 2 regardless of score if nothing is selected
            selected = [sent for _, sent in scored_sentences[:2]]
            
        compressed_text = " ... ".join(selected)
        compressed_docs.append({
            "company": doc["company"],
            "section": doc["section"],
            "chunk_index": doc["chunk_index"],
            "text": compressed_text
        })
            
    print(f"[NODE] Compressed {len(documents)} docs")
    return {"compressed_documents": compressed_docs}


def rewrite_query(state: dict) -> dict:
    """Node: Rewrite the question for better search results."""
    question = state["question"]
    retry_count = state.get("retry_count", 0)
    print(f"[NODE] Rewrite Query (retry {retry_count})")

    llm = get_llm(temperature=0.5)
    prompt = f"""Bạn là chuyên gia tìm kiếm tài chính.

Câu hỏi gốc không tìm được tài liệu phù hợp: "{question}"

Hãy viết lại câu hỏi bằng tiếng Anh, tập trung vào từ khóa tài chính quan trọng.
Chỉ trả về câu hỏi mới, không giải thích."""

    try:
        response = llm.invoke(prompt)
        rewritten = response.content.strip()
        print(f"[NODE] Rewritten: '{rewritten[:80]}'")
        return {"question": rewritten, "retry_count": retry_count + 1}
    except Exception:
        return {"retry_count": retry_count + 1}


def search_web(state: dict) -> dict:
    """Node: Search web using Tavily for additional information."""
    question = state["question"]
    print(f"[NODE] Search Web: '{question[:60]}'")

    results = search_web_tavily(question, max_results=3)
    print(f"[NODE] Web results: {len(results)} chars")

    return {"web_results": results}


def assess_need_sql(state: dict) -> dict:
    """Node: Assess if we need SQL data to answer the question."""
    question = state["question"]
    documents = state.get("documents", [])
    print(f"[NODE] Assess Need SQL")

    # Pass-through node — routing logic is in the conditional edge
    return {}


def query_sql(state: dict) -> dict:
    """Node: Generate and execute SQL query using LLM."""
    question = state["question"]
    print(f"[NODE] Query SQL")

    llm = get_llm(temperature=0.1)
    prompt = f"""You are a SQL expert. Generate a PostgreSQL SELECT query to answer the question.

{DB_SCHEMA}

Rules:
- ONLY generate SELECT queries.
- Return ONLY the SQL query, no explanation, no markdown.
- Ticker symbols are UPPERCASE (e.g., 'AAPL').
- LIMIT results to 20 rows unless asked for more.
- For date comparisons, use 'YYYY-MM-DD' format.
- If asked about a company by name, look up its ticker.

Question: {question}

SQL:"""

    try:
        response = llm.invoke(prompt)
        sql = response.content.strip().replace("```sql", "").replace("```", "").strip()
        print(f"[NODE] Generated SQL: {sql[:100]}")

        result = execute_sql_query(sql)
        result_str = f"Columns: {result['columns']}\nData: {result['rows'][:10]}"
        return {"sql_query": sql, "sql_result": result_str}
    except Exception as e:
        print(f"[NODE] SQL Error: {e}")
        return {"sql_query": "", "sql_result": f"SQL Error: {str(e)[:200]}"}


def generate_answer(state: dict) -> dict:
    """Node: Generate final answer combining all available information."""
    question = state["question"]
    documents = state.get("compressed_documents", state.get("documents", []))
    sql_result = state.get("sql_result", "")
    web_results = state.get("web_results", "")
    messages = state.get("messages", [])
    print(f"[NODE] Generate Answer")

    # Build context from all sources
    context_parts = []

    if documents:
        doc_texts = []
        for d in documents[:3]:
            doc_texts.append(f"[{d['company']} - {d['section']}]: {d['text'][:500]}")
        context_parts.append("[DOC] Tai lieu bao cao:\n" + "\n\n".join(doc_texts))

    if sql_result and "Error" not in sql_result:
        context_parts.append(f"[SQL] Ket qua SQL:\n{sql_result}")

    if web_results and "Lỗi" not in web_results:
        context_parts.append(f"[WEB] Ket qua web:\n{web_results[:500]}")

    # Build conversation history
    history_text = ""
    if messages and len(messages) > 1:
        recent = messages[-6:]  # Last 3 turns
        history_parts = []
        for m in recent:
            role = "User" if m.type == "human" else "Agent"
            history_parts.append(f"{role}: {m.content[:200]}")
        history_text = f"\nLịch sử hội thoại:\n" + "\n".join(history_parts)

    context = "\n\n".join(context_parts) if context_parts else "Không có thông tin."

    llm = get_llm(temperature=0.35)
    prompt = f"""Bạn là trợ lý phân tích tài chính DJIA (Dow Jones Industrial Average).

Yêu cầu:
- Trả lời bằng TIẾNG VIỆT, tự nhiên, rõ ràng, ngắn gọn.
- KHÔNG lặp lại câu hỏi.
- Chỉ dùng thông tin có trong context, không bịa thêm.
- Nếu có số liệu, format dễ đọc.
- Kết thúc bằng nguồn: 📌 Nguồn: [loại nguồn phù hợp]
- Nếu không đủ thông tin, nói rõ và gợi ý câu hỏi khác.
{history_text}

Câu hỏi: {question}

Context:
{context}"""

    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()
    except Exception as e:
        print(f"[GENERATE] LLM Error: {e}")
        # Smart fallback — format structured summary instead of raw text
        if sql_result and "Error" not in sql_result:
            answer = f"{sql_result}\n\n📌 Nguồn: Cơ sở dữ liệu cổ phiếu DJIA"
        elif documents:
            company = documents[0]["company"]
            sections = list({d["section"] for d in documents})
            # Pick the best excerpt — skip boilerplate, find meaningful text
            best_text = ""
            for d in documents:
                text = d["text"].strip()
                # Skip chunks that look like SEC headers or legal boilerplate
                boilerplate_markers = [
                    "UNITED STATES", "SECURITIES AND EXCHANGE", "FORM 10-K", 
                    "TABLE OF CONTENTS", "Exchange Act", "forward-looking", 
                    "Securities Act", "Item 1A.", "Item 1."
                ]
                if any(h.lower() in text[:300].lower() for h in boilerplate_markers):
                    continue
                best_text = text[:600]
                break
            
            if not best_text:
                # If all chunks look like boilerplate, pick the last one (usually deepest in doc)
                best_text = documents[-1]["text"][:600]
                
            answer = (
                f"📊 **{company}** — Thông tin từ báo cáo thường niên (10-K)\n\n"
                f"📂 Các phần liên quan: {', '.join(sections)}\n\n"
                f"{best_text}...\n\n"
                f"📌 Nguồn: Báo cáo thường niên ({company})\n"
                f"⚠️ *Lưu ý: AI đang bận, hiển thị trích dẫn trực tiếp từ báo cáo.*"
            )
        else:
            answer = "Xin lỗi, hiện không thể xử lý câu hỏi. Vui lòng thử lại sau."

    return {
        "generation": answer,
        "messages": [AIMessage(content=answer)],
    }


# ──────────────────────────────────────────────
# Conditional Edge Functions
# ──────────────────────────────────────────────

def route_after_grade(state: dict) -> str:
    """Decide next step after grading documents."""
    documents = state.get("documents", [])
    retry_count = state.get("retry_count", 0)

    if documents:
        print("[ROUTE] Docs relevant -> compress")
        return "compress"
    elif retry_count < 1:
        print("[ROUTE] No relevant docs -> rewrite")
        return "rewrite"
    else:
        print("[ROUTE] Max retries -> fallback to web search")
        return "search_web"


def route_after_assess(state: dict) -> str:
    """Decide if SQL query is needed."""
    question = state.get("question", "").lower()

    sql_indicators = [
        "price", "closing", "opening", "high", "low", "volume",
        "average", "max", "min", "compare", "highest", "lowest",
        "sector", "industry", "how many", "count", "market cap",
        "giá", "đóng cửa", "mở cửa", "cao nhất", "thấp nhất",
        "khối lượng", "trung bình", "so sánh", "lĩnh vực", "bao nhiêu",
    ]

    if any(kw in question for kw in sql_indicators):
        print("[ROUTE] Need SQL -> query_sql")
        return "query_sql"

    print("[ROUTE] Route to Generate")
    return "generate"
