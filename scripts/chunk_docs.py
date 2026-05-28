"""
Chunk cleaned text documents and batch-insert into Supabase rag_chunks table.
Uses multi-row INSERT for performance on remote Supabase.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "backend" / ".env")
sys.path.insert(0, str(BASE_DIR / "backend"))

import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True,
                       connect_args={"connect_timeout": 60})

INPUT_DIR = BASE_DIR / "data" / "rag_text_clean"
CHUNK_SIZE = 1800
OVERLAP = 250
BATCH_SIZE = 50  # rows per INSERT

TICKER_COMPANY_MAP = {
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


def split_text(txt):
    chunks, start = [], 0
    while start < len(txt):
        chunk = txt[start:start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - OVERLAP
    return chunks


def infer_company(filename):
    stem = Path(filename).stem.upper()
    if stem in TICKER_COMPANY_MAP:
        return TICKER_COMPANY_MAP[stem]
    for ticker, company in TICKER_COMPANY_MAP.items():
        if stem.startswith(ticker):
            return company
    return stem


def infer_section(txt):
    lower = txt.lower()
    if "risk factors" in lower or "item 1a" in lower:
        return "Risk Factors"
    if "item 1. business" in lower or "\nbusiness\n" in lower:
        return "Business"
    if "management" in lower and "discussion" in lower:
        return "MD&A"
    if "segment" in lower:
        return "Segments"
    return "General"


def batch_insert_chunks(conn, rows):
    """Insert multiple chunk rows in one SQL statement."""
    if not rows:
        return
    parts = []
    params = {}
    for i, (doc_id, company, section, chunk, idx) in enumerate(rows):
        parts.append(f"(:d{i}, :c{i}, :s{i}, :t{i}, :x{i})")
        params[f"d{i}"] = doc_id
        params[f"c{i}"] = company
        params[f"s{i}"] = section
        params[f"t{i}"] = chunk
        params[f"x{i}"] = idx
    sql = ("INSERT INTO rag_chunks (document_id, company, section, chunk_text, chunk_index) "
           "VALUES " + ", ".join(parts))
    conn.execute(text(sql), params)


def main():
    files = sorted(INPUT_DIR.glob("*.txt"))
    if not files:
        print(f"No text files found in {INPUT_DIR}")
        return

    print(f"Found {len(files)} files to process")

    # Clear old data
    print("Clearing old RAG data...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM rag_chunks"))
        conn.execute(text("DELETE FROM rag_documents"))
    print("  [OK] Old data cleared")

    total_chunks = 0
    for i, file in enumerate(files):
        content = file.read_text(encoding="utf-8", errors="ignore")
        company = infer_company(file.name)
        chunks = split_text(content)

        with engine.begin() as conn:
            # Insert document
            result = conn.execute(
                text("INSERT INTO rag_documents (company, doc_type, source_file, content) "
                     "VALUES (:company, 'annual_report_10k', :source, :content) RETURNING id"),
                {"company": company, "source": file.name, "content": content[:50000]}
            )
            doc_id = result.fetchone()[0]

            # Batch insert chunks
            batch = []
            for idx, chunk in enumerate(chunks):
                section = infer_section(chunk)
                batch.append((doc_id, company, section, chunk, idx))
                if len(batch) >= BATCH_SIZE:
                    batch_insert_chunks(conn, batch)
                    batch = []
            if batch:
                batch_insert_chunks(conn, batch)

        total_chunks += len(chunks)
        print(f"  [{i+1}/{len(files)}] {file.name} -> {company} | {len(chunks)} chunks")

    print(f"\nDone! {len(files)} files -> {total_chunks} total chunks in Supabase")


if __name__ == "__main__":
    main()