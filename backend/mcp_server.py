"""
MCP Server — Expose LangGraph agent tools for Claude integration
"""
import os
from dotenv import load_dotenv

# Đảm bảo load đúng file .env nằm chung thư mục với mcp_server.py
# (Claude Desktop thường gọi script từ thư mục khác nên phải dùng đường dẫn tuyệt đối)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

from mcp.server.fastmcp import FastMCP
from tools import execute_sql_query, search_rag_chunks, search_web_tavily, detect_company
from langchain_core.messages import HumanMessage
from graph import graph
from memory import get_thread_config
import uuid

mcp = FastMCP("DJIA Financial Agent MCP Server")


@mcp.tool()
def query_stock_sql(sql: str) -> str:
    """
    Run a read-only SQL query on DJIA stock data.
    Tables: companies (symbol, name, sector, ...), prices (trade_date, open, high, low, close, volume, ticker)
    """
    try:
        result = execute_sql_query(sql)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def search_company_report(question: str) -> str:
    """
    Search annual report chunks for all 30 DJIA companies.
    Searches through 10-K annual reports stored in the database.
    """
    docs = search_rag_chunks(question, limit=5)
    return str(docs)


@mcp.tool()
def search_financial_web(query: str) -> str:
    """
    Search the web for financial information using Tavily.
    """
    return search_web_tavily(query, max_results=3)


@mcp.tool()
def ask_financial_agent(question: str) -> str:
    """
    Ask the LangGraph financial agent a natural-language question.
    The agent will automatically retrieve documents, query SQL, and search the web.
    """
    session_id = str(uuid.uuid4())
    config = get_thread_config(session_id)

    result = graph.invoke(
        {
            "question": question,
            "messages": [HumanMessage(content=question)],
            "documents": [],
            "web_results": "",
            "sql_result": "",
            "sql_query": "",
            "generation": "",
            "retry_count": 0,
        },
        config,
    )
    return result.get("generation", "No answer generated")


if __name__ == "__main__":
    mcp.run()