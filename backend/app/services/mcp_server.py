"""
Model Context Protocol (MCP) Server for NIFTY-Pulse Platform.
Provides JSON-RPC 2.0 standard tool declarations and dispatch handlers so that
external AI agents and LLMs can interact with NIFTY50 market intelligence.
"""
from typing import Dict, Any, List
from backend.app.services.market_data import market_data_service
from backend.app.services.rag_engine import rag_engine
from backend.app.services.alerts_engine import alerts_engine
from backend.app.models.schemas import RAGQueryRequest
from backend.app.guardrails.compliance import SEBI_MANDATORY_DISCLAIMER


MCP_TOOLS_SPEC = [
    {
        "name": "get_nifty_quote",
        "description": "Fetch real-time price, day high/low, volume, and percentage change for a NIFTY50 stock or index.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker symbol, e.g. 'RELIANCE', 'TCS', 'ADANIENT', or 'NIFTY50'"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_nifty50_heatmap",
        "description": "Retrieve sector-by-sector performance and top gainers/losers across all 50 constituent companies.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_fii_dii_flows",
        "description": "Get latest Foreign & Domestic Institutional Investor net cash flows and Index Futures Long/Short derivative positioning.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_leadership_signals",
        "description": "Inspect policy speeches, bilateral summits, and announcements by Indian PM Modi, FM Sitharaman, and EAM Jaishankar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "leader_filter": {"type": "string", "description": "Optional filter: 'MODI', 'SITHARAMAN', 'JAISHANKAR'"}
            }
        }
    },
    {
        "name": "get_conglomerate_activity",
        "description": "Track strategic capex, joint ventures, and debt profiles for Reliance Industries (Ambani) and Adani Group.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "group_filter": {"type": "string", "description": "'RELIANCE' or 'ADANI'"}
            }
        }
    },
    {
        "name": "get_asset_manager_moves",
        "description": "Track institutional portfolio weight shifts and ETF flows from BlackRock (INDA) and Vanguard.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "firm": {"type": "string", "description": "'BLACKROCK' or 'VANGUARD'"}
            }
        }
    },
    {
        "name": "run_quantitative_cycle_backtest",
        "description": "Execute statistical hypothesis testing on astronomical / calendar cycles against historical NIFTY50 volatility and returns (SEBI-compliant empirical quantitative analysis).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cycle_type": {"type": "string", "enum": ["lunar_synodic", "solar_seasonal", "planetary_retrograde"], "description": "Type of cycle to empirically test"}
            },
            "required": ["cycle_type"]
        }
    },
    {
        "name": "query_rag_knowledgebase",
        "description": "Query official leadership speeches, corporate filings, and macro intelligence with citation grounding.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Financial research question"}
            },
            "required": ["query"]
        }
    }
]


class MCPServer:
    """
    Handles MCP JSON-RPC 2.0 requests.
    """

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns MCP tool definitions."""
        return MCP_TOOLS_SPEC

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an MCP tool call and returns the result."""
        try:
            if name == "get_nifty_quote":
                sym = arguments.get("symbol", "NIFTY50").upper()
                if sym in ["NIFTY", "NIFTY50", "^NSEI"]:
                    indices = market_data_service.get_market_indices()
                    return {
                        "symbol": "NIFTY50",
                        "price": indices.nifty50_price,
                        "change": indices.nifty50_change,
                        "change_percent": indices.nifty50_change_percent,
                        "market_status": indices.market_status,
                    }
                quote = market_data_service.get_stock_quote(sym)
                if quote:
                    return quote.model_dump()
                return {"error": f"Symbol {sym} not found in NIFTY50 constituent database."}

            elif name == "get_nifty50_heatmap":
                return market_data_service.get_sector_breakdown()

            elif name == "get_fii_dii_flows":
                # Static snapshot or linked to fii_dii_agent
                return {
                    "date": "2024-10-15",
                    "fii_cash_net_cr": -1245.50,
                    "dii_cash_net_cr": 2180.20,
                    "fii_long_short_ratio": 0.58,
                    "institutional_signal": "BULLISH DII ABSORPTION / FII SHORT COVERING",
                    "compliance": SEBI_MANDATORY_DISCLAIMER
                }

            elif name == "query_rag_knowledgebase":
                q = arguments.get("query", "")
                res = rag_engine.query(RAGQueryRequest(query=q))
                return res.model_dump()

            elif name == "get_leadership_signals":
                from backend.app.agents.leadership_agent import leadership_agent
                return {"events": [e.model_dump() for e in leadership_agent.get_latest_events()]}

            elif name == "get_conglomerate_activity":
                from backend.app.agents.conglomerate_agent import conglomerate_agent
                grp = arguments.get("group_filter")
                return {"updates": [u.model_dump() for u in conglomerate_agent.get_latest_updates(grp)]}

            elif name == "get_asset_manager_moves":
                from backend.app.agents.asset_manager_agent import asset_manager_agent
                return {"updates": [u.model_dump() for u in asset_manager_agent.get_latest_updates()]}

            elif name == "run_quantitative_cycle_backtest":
                from backend.app.agents.quantitative_cycle_agent import quant_cycle_agent
                cycle = arguments.get("cycle_type", "lunar_synodic")
                return quant_cycle_agent.get_backtest_result(cycle).model_dump()

            else:
                return {"error": f"Tool '{name}' is not recognized."}

        except Exception as e:
            return {"error": f"Error executing tool '{name}': {str(e)}"}

    def handle_jsonrpc(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handles standard JSON-RPC 2.0 MCP protocol envelopes."""
        req_id = request_data.get("id")
        method = request_data.get("method")
        params = request_data.get("params", {})

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self.list_tools()}}
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            res = self.execute_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": str(res)}], "data": res}
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found."}
            }


# Singleton instance
mcp_server = MCPServer()
