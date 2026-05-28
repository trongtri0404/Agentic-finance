"""
Database Connection — Supabase PostgreSQL via SQLAlchemy
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def run_sql(sql: str, params: dict | None = None):
    """Execute SQL query and return results."""
    with engine.begin() as conn:
        result = conn.execute(text(sql), params or {})
        if result.returns_rows:
            rows = result.fetchall()
            cols = list(result.keys())
            return {"columns": cols, "rows": [list(r) for r in rows]}
        return {"columns": [], "rows": []}