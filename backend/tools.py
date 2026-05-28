"""
LangGraph Tools — SQL, RAG, Web Search
"""
import os
import re
from dotenv import load_dotenv
from db import run_sql

load_dotenv()

# ──────────────────────────────────────────────
# Ticker ↔ Company mapping (30 DJIA companies)
# ──────────────────────────────────────────────
TICKER_MAP = {
    "apple": "AAPL", "aapl": "AAPL",
    "amgen": "AMGN", "amgn": "AMGN",
    "american express": "AXP", "axp": "AXP",
    "boeing": "BA", "ba": "BA",
    "caterpillar": "CAT", "cat": "CAT",
    "salesforce": "CRM", "crm": "CRM",
    "cisco": "CSCO", "csco": "CSCO",
    "chevron": "CVX", "cvx": "CVX",
    "disney": "DIS", "dis": "DIS",
    "dow": "DOW",
    "goldman sachs": "GS", "goldman": "GS", "gs": "GS",
    "home depot": "HD", "hd": "HD",
    "honeywell": "HON", "hon": "HON",
    "ibm": "IBM",
    "intel": "INTC", "intc": "INTC",
    "johnson & johnson": "JNJ", "j&j": "JNJ", "jnj": "JNJ",
    "jpmorgan": "JPM", "jpm": "JPM",
    "coca-cola": "KO", "coca cola": "KO", "ko": "KO",
    "mcdonald's": "MCD", "mcdonalds": "MCD", "mcd": "MCD",
    "3m": "MMM", "mmm": "MMM",
    "merck": "MRK", "mrk": "MRK",
    "microsoft": "MSFT", "msft": "MSFT",
    "nike": "NKE", "nke": "NKE",
    "procter & gamble": "PG", "p&g": "PG", "pg": "PG",
    "travelers": "TRV", "trv": "TRV",
    "unitedhealth": "UNH", "unh": "UNH",
    "visa": "V",
    "verizon": "VZ", "vz": "VZ",
    "walgreens": "WBA", "wba": "WBA",
    "walmart": "WMT", "wmt": "WMT",
}

TICKER_TO_COMPANY = {
    "AAPL": "Apple", "AMGN": "Amgen", "AXP": "American Express",
    "BA": "Boeing", "CAT": "Caterpillar", "CRM": "Salesforce",
    "CSCO": "Cisco", "CVX": "Chevron", "DIS": "Disney", "DOW": "Dow",
    "GS": "Goldman Sachs", "HD": "Home Depot", "HON": "Honeywell",
    "IBM": "IBM", "INTC": "Intel", "JNJ": "Johnson & Johnson",
    "JPM": "JPMorgan", "KO": "Coca-Cola", "MCD": "McDonald's",
    "MMM": "3M", "MRK": "Merck", "MSFT": "Microsoft", "NKE": "Nike",
    "PG": "Procter & Gamble", "TRV": "Travelers", "UNH": "UnitedHealth",
    "V": "Visa", "VZ": "Verizon", "WBA": "Walgreens", "WMT": "Walmart",
}

DB_SCHEMA = """
Tables in the database:

1. companies (symbol VARCHAR PRIMARY KEY, name VARCHAR, sector VARCHAR, industry VARCHAR,
   country VARCHAR, website VARCHAR, market_cap DOUBLE PRECISION, pe_ratio DOUBLE PRECISION,
   dividend_yield DOUBLE PRECISION, week_52_high DOUBLE PRECISION, week_52_low DOUBLE PRECISION,
   description TEXT)

2. prices (trade_date DATE, open DOUBLE PRECISION, high DOUBLE PRECISION, low DOUBLE PRECISION,
   close DOUBLE PRECISION, volume BIGINT, dividends DOUBLE PRECISION, stock_splits DOUBLE PRECISION,
   ticker VARCHAR)
   -- ticker is the stock symbol, e.g. 'AAPL', 'MSFT', 'BA', 'KO', etc.
   -- trade_date format: YYYY-MM-DD

Common ticker-company mappings:
AAPL=Apple, AMGN=Amgen, AXP=American Express, BA=Boeing, CAT=Caterpillar,
CRM=Salesforce, CSCO=Cisco, CVX=Chevron, DIS=Disney, DOW=Dow,
GS=Goldman Sachs, HD=Home Depot, HON=Honeywell, IBM=IBM, INTC=Intel,
JNJ=Johnson & Johnson, JPM=JPMorgan, KO=Coca-Cola, MCD=McDonald's, MMM=3M,
MRK=Merck, MSFT=Microsoft, NKE=Nike, PG=Procter & Gamble, TRV=Travelers,
UNH=UnitedHealth, V=Visa, VZ=Verizon, WBA=Walgreens, WMT=Walmart
"""


# ──────────────────────────────────────────────
# Tool functions (called by graph nodes)
# ──────────────────────────────────────────────

def detect_company(question: str) -> str | None:
    """Detect company name from question text."""
    q = question.lower()
    for key, ticker in TICKER_MAP.items():
        if key in q:
            return TICKER_TO_COMPANY.get(ticker, ticker)
    return None


def search_rag_chunks(question: str, limit: int = 5) -> list[dict]:
    """Search RAG chunks from Supabase rag_chunks table with relevance ranking."""
    company = detect_company(question)

    # Extract keywords — expanded stop words for Vietnamese
    stop_words = {
        "what", "is", "the", "of", "in", "a", "an", "and", "or", "to",
        "does", "do", "how", "which", "are", "its", "their", "about",
        "for", "that", "this", "with", "from", "has", "have", "been",
        "gì", "là", "của", "trong", "và", "hay", "những", "các", "cho",
        "có", "không", "nào", "với", "từ", "này", "đó", "được", "như",
        "kinh", "doanh", "công", "thế", "thì", "đã", "sẽ", "bao", "nhiêu",
    }
    
    # Simple Vietnamese to English mapping for better RAG matching on 10-K docs
    vi_to_en = {
        "sản": "product", "phẩm": "product",
        "rủi": "risk", "ro": "risk",
        "doanh": "revenue", "thu": "revenue",
        "lợi": "profit", "nhuận": "profit",
        "chiến": "strategy", "lược": "strategy",
        "đối": "competitor", "thủ": "competitor",
        "thị": "market", "trường": "market",
        "tài": "financial", "chính": "financial",
        "nhân": "employee", "sự": "employee", "viên": "employee",
        "bán": "sales", "hàng": "sales",
        "phát": "development", "triển": "development",
        "tương": "future", "lai": "future",
        "dịch": "service", "vụ": "service",
        "tiền": "cash", "vốn": "capital",
        "mục": "objective", "tiêu": "objective",
    }
    
    words = [w.strip("?.!,") for w in question.lower().split() if len(w) > 2]
    keywords = []
    for w in words:
        if w not in stop_words:
            # Map to English if possible, else keep original
            en_w = vi_to_en.get(w, w)
            if en_w not in keywords:
                keywords.append(en_w)
    keywords = keywords[:5]

    params = {}
    where_parts = []

    if company:
        where_parts.append("lower(company) = lower(:company)")
        params["company"] = company
        # Remove company name from keywords to avoid boosting boilerplate that says the name
        company_parts = set(company.lower().split())
        keywords = [kw for kw in keywords if kw.lower() not in company_parts]

    if keywords:
        kw_clauses = []
        for i, kw in enumerate(keywords):
            key = f"kw{i}"
            kw_clauses.append(f"lower(chunk_text) LIKE lower(:{key})")
            params[key] = f"%{kw}%"
        where_parts.append(f"({' OR '.join(kw_clauses)})")

    # Skip header chunks (first 3 chunks are always SEC filing boilerplate)
    where_parts.append("chunk_index > 2")

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    # Build relevance score: count how many keywords match each chunk
    if keywords:
        score_parts = []
        for i in range(len(keywords)):
            key = f"kw{i}"
            score_parts.append(f"CASE WHEN lower(chunk_text) LIKE lower(:{key}) THEN 1 ELSE 0 END")
        score_sql = " + ".join(score_parts)
        order_sql = f"ORDER BY ({score_sql}) DESC, chunk_index ASC"
    else:
        order_sql = "ORDER BY chunk_index ASC"

    sql = (f"SELECT company, section, chunk_index, chunk_text "
           f"FROM rag_chunks {where_sql} {order_sql} LIMIT :lim")
    # Fetch more chunks initially, then filter out boilerplate
    params["lim"] = limit * 4  # Fetch extra to filter

    try:
        result = run_sql(sql, params)
        docs = []
        for row in result["rows"]:
            text = row[3].strip()
            is_boilerplate = False

            # Skip very short chunks (likely just headings)
            if len(text) < 100:
                is_boilerplate = True

            # Skip SEC filing headers
            header_markers = [
                "UNITED STATES", "SECURITIES AND EXCHANGE COMMISSION",
                "FORM 10-K", "Exact name of registrant",
                "Commission file number", "Commission File Number",
                "(State of incorporation", "(State or other jurisdiction",
            ]
            if any(m in text[:300] for m in header_markers):
                is_boilerplate = True

            # Skip Table of Contents chunks — detect by counting "Item X." patterns
            import re
            item_count = len(re.findall(r"Item\s+\d+[A-C]?\.", text))
            if item_count >= 4:
                is_boilerplate = True

            # Skip chunks that are mostly section headings (many short lines)
            lines = text.split("\n")
            short_lines = sum(1 for l in lines if 0 < len(l.strip()) < 60)
            if len(lines) > 5 and short_lines / len(lines) > 0.7:
                is_boilerplate = True

            if not is_boilerplate:
                docs.append({
                    "company": row[0],
                    "section": row[1],
                    "chunk_index": row[2],
                    "text": text[:1500],
                })
            if len(docs) >= limit:
                break

        print(f"[RAG] Found {len(docs)} chunks, sections: {[d['section'] for d in docs]}")
        return docs
    except Exception as e:
        print(f"[RAG] Error: {e}")
        return []


def execute_sql_query(sql_query: str) -> dict:
    """Execute a read-only SQL query on the stock database."""
    q = sql_query.strip().lower()
    if not (q.startswith("select") or q.startswith("with")):
        raise ValueError("Only SELECT/WITH queries are allowed.")
    return run_sql(sql_query)


def search_web_tavily(query: str, max_results: int = 3) -> str:
    """Search the web using Tavily API."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.search(query, max_results=max_results)
        results = []
        for r in response.get("results", []):
            results.append(f"**{r['title']}**\n{r['content'][:300]}\nURL: {r['url']}")
        return "\n\n---\n\n".join(results) if results else "Không tìm thấy kết quả."
    except Exception as e:
        print(f"[TAVILY] Error: {e}")
        return f"Lỗi tìm kiếm web: {str(e)[:100]}"
