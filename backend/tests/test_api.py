"""
Integration tests for FastAPI endpoints, RAG semantic search, and MCP tools.
"""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_probe():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["active_agents"] == 6


def test_market_indices():
    response = client.get("/api/market/indices")
    assert response.status_code == 200
    data = response.json()
    assert "nifty50_price" in data
    assert data["nifty50_price"] > 20000


def test_quotes():
    response = client.get("/api/market/quotes")
    assert response.status_code == 200
    quotes = response.json()
    assert len(quotes) == 50
    symbols = [q["symbol"] for q in quotes]
    assert "RELIANCE" in symbols
    assert "ADANIENT" in symbols


def test_rag_query():
    payload = {"query": "What did PM Modi say about semiconductors?", "top_k": 3}
    response = client.post("/api/rag/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["citations"]) > 0
    assert "Semiconductor" in data["synthesized_answer"]


def test_mcp_tools():
    # 1. List tools
    req_list = {"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}}
    resp = client.post("/api/mcp", json=req_list)
    assert resp.status_code == 200
    tools = resp.json()["result"]["tools"]
    assert any(t["name"] == "get_nifty_quote" for t in tools)

    # 2. Call tool
    req_call = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/call",
        "params": {"name": "get_nifty_quote", "arguments": {"symbol": "RELIANCE"}}
    }
    resp = client.post("/api/mcp", json=req_call)
    assert resp.status_code == 200
    res = resp.json()["result"]["data"]
    assert res["symbol"] == "RELIANCE"
