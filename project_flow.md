# 📊 Sơ đồ luồng chạy Project Agentic Finance

## 1. Luồng chạy chính (Agent Flow)

```mermaid
flowchart LR
    Q["❓ Question"]:::input --> R["🔀 Router<br/>(classify_question)"]:::router
    
    R -->|"SQL Route"| GEN["⚡ Generate SQL<br/>(Gemini AI)"]:::gemini
    GEN --> DB["🗄️ Query Database<br/>(PostgreSQL)"]:::db
    DB --> FMT["📝 Format Answer<br/>(Gemini AI)"]:::gemini
    FMT --> RES["✅ Response"]:::output
    
    R -->|"RAG Route"| DET["🏢 Detect Company"]:::process
    DET --> SEARCH["🔍 Search Documents<br/>(RAG Chunks)"]:::db
    SEARCH --> SMOOTH["📝 Smooth Answer<br/>(Gemini AI)"]:::gemini
    SMOOTH --> RES
    
    R -->|"Greeting Route"| GREET["👋 Welcome Message"]:::output
    GREET --> RES
    
    classDef input fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef router fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef gemini fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef db fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef process fill:#fce4ec,stroke:#c62828,stroke-width:2px,color:#000
    classDef output fill:#e0f7fa,stroke:#00838f,stroke-width:2px,color:#000
```

---

## 2. Data Pipeline (Tiền xử lý dữ liệu)

```mermaid
flowchart LR
    HTML["📄 HTML Reports<br/>(SEC 10-K)"]:::input --> PARSE["🔧 Parse HTML<br/>(parse_html_docs.py)"]:::process
    PARSE --> CLEAN["🧹 Clean Text<br/>(clean_rag_txt.py)"]:::process
    CLEAN --> CHUNK["✂️ Chunk Documents<br/>(chunk_docs.py)"]:::process
    CHUNK --> RAGDB["🗄️ rag_chunks<br/>(PostgreSQL)"]:::db
    
    CSV["📊 CSV Data<br/>(Yahoo Finance)"]:::input --> LOAD["📥 Load Data<br/>(load_data.py)"]:::process
    LOAD --> SQLDB["🗄️ companies + prices<br/>(PostgreSQL)"]:::db
    
    classDef input fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef process fill:#fff8e1,stroke:#f57f17,stroke-width:2px,color:#000
    classDef db fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000
```

---

## 3. Kiến trúc tổng thể

```mermaid
flowchart TB
    subgraph FE["🖥️ Frontend (React + Vite)"]
        UI["Chat UI<br/>App.jsx"]
    end
    
    subgraph BE["⚙️ Backend (FastAPI)"]
        API["main.py<br/>POST /chat"]
        AGENT["agent.py<br/>run_agent()"]
        ROUTER["router.py<br/>classify_question()"]
        
        subgraph TOOLS["🔧 Tools"]
            SQL_TOOL["sql_tool.py"]
            RAG_TOOL["rag_tool.py"]
        end
        
        GEMINI["gemini_smoother.py<br/>Gemini AI"]
    end
    
    subgraph DATA["🗄️ Database (Supabase)"]
        COMPANIES["companies<br/>(30 công ty)"]
        PRICES["prices<br/>(15,060 rows)"]
        RAG["rag_chunks<br/>(957 chunks)"]
        LOGS["request_logs"]
    end
    
    UI -->|"POST /chat"| API
    API --> AGENT
    AGENT --> ROUTER
    ROUTER --> SQL_TOOL
    ROUTER --> RAG_TOOL
    SQL_TOOL --> COMPANIES
    SQL_TOOL --> PRICES
    RAG_TOOL --> RAG
    AGENT --> GEMINI
    AGENT --> LOGS
    
    style FE fill:#1a237e,stroke:#283593,color:#fff
    style BE fill:#1b5e20,stroke:#2e7d32,color:#fff
    style DATA fill:#e65100,stroke:#f57c00,color:#fff
    style TOOLS fill:#004d40,stroke:#00695c,color:#fff
```

---

## 4. Luồng chi tiết từng bước

| Bước | Component | File | Mô tả |
|------|-----------|------|-------|
| 1 | User nhập câu hỏi | `App.jsx` | Frontend gửi POST request |
| 2 | API nhận request | `main.py` | FastAPI endpoint `/chat` |
| 3 | Phân loại câu hỏi | `router.py` | Keyword-based → `sql`, `rag`, hoặc `greeting` (Hỗ trợ từ khóa tiếng Việt) |
| 4a | **SQL**: Sinh SQL | `agent.py` | Gemini AI sinh câu SQL. Có tích hợp **Fallback SQL** dự phòng khi LLM quá tải (nhận diện cao nhất/thấp nhất, khối lượng/giá). |
| 4b | **RAG**: Tìm company | `rag_tool.py` | Detect company từ câu hỏi |
| 4c | **Greeting**: Xử lý | `agent.py` | Trả về lời chào thân thiện |
| 5a | **SQL**: Truy vấn DB | `sql_tool.py` | Chạy SQL trên PostgreSQL |
| 5b | **RAG**: Tìm chunks | `rag_tool.py` | Tìm chunks phù hợp trong DB |
| 6 | Format câu trả lời | `agent.py` / `gemini_smoother.py` | Gemini viết lại bằng tiếng Việt (Hoặc Fallback RAW nếu lỗi) |
| 7 | Ghi log | `agent.py` | Lưu vào `request_logs` |
| 8 | Trả kết quả | `main.py` → `App.jsx` | JSON response → hiển thị chat |

![Project Flow Diagram](file:///C:/Users/TRONG%20TRI/.gemini/antigravity/brain/08de5c97-a697-4e22-a1d4-6982f99448c8/project_flow_diagram_1773986900081.png)
