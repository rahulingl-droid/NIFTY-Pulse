"""
NIFTY-Pulse FastAPI Main Server.
Real-Time Multi-Agent NIFTY50 Intelligence, Quantitative Surveillance & Ephemeris Platform.
Equipped with WebSockets, RAG, MCP, SEBI Compliance Guardrails, and Azure Cloud Probes.
"""
import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from backend.app.config import config
from backend.app.models.schemas import (
    StockQuote,
    MarketIndices,
    FiiDiiRecord,
    MarketNewsItem,
    LeadershipEvent,
    ConglomerateUpdate,
    AssetManagerUpdate,
    QuantitativeCycleResult,
    MarketAlert,
    RAGQueryRequest,
    RAGQueryResponse,
    SystemHealth,
    SeverityLevel,
)
from backend.app.services.market_data import market_data_service
from backend.app.services.rag_engine import rag_engine
from backend.app.services.alerts_engine import alerts_engine
from backend.app.services.mcp_server import mcp_server
from backend.app.agents.orchestrator import master_orchestrator
from backend.app.agents.news_agent import market_news_agent
from backend.app.agents.fii_dii_agent import institutional_flow_agent
from backend.app.agents.leadership_agent import leadership_agent
from backend.app.agents.conglomerate_agent import conglomerate_agent
from backend.app.agents.asset_manager_agent import asset_manager_agent
from backend.app.agents.quantitative_cycle_agent import quant_cycle_agent
from backend.app.guardrails.compliance import ComplianceGuardrail, SEBI_MANDATORY_DISCLAIMER
from backend.app.guardrails.security import SecurityGuardrail

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")


# Background loop handles
_background_tasks = []


async def market_ticker_loop():
    """Streams live market index ticks and price fluctuations over WebSockets."""
    while True:
        try:
            await asyncio.sleep(config.MARKET_TICK_INTERVAL_SEC)
            quotes = market_data_service.refresh_quotes()
            indices = market_data_service.get_market_indices()
            
            tick_payload = {
                "indices": indices.model_dump(),
                "top_tickers": [quotes["RELIANCE"].model_dump(), quotes["TCS"].model_dump(), quotes["HDFCBANK"].model_dump(), quotes["ADANIENT"].model_dump()],
                "server_time": datetime.utcnow().isoformat(),
            }
            await alerts_engine.broadcast_market_tick(tick_payload)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Tick loop error: {e}")


async def scheduled_agent_scan_loop():
    """Runs periodic multi-agent scans to refresh synthesized intelligence."""
    while True:
        try:
            await asyncio.sleep(config.AGENT_SCAN_INTERVAL_SEC)
            await master_orchestrator.run_full_scan()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Scheduled agent scan loop error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: starts background market ticking and agent scheduling."""
    logger.info("Starting NIFTY-Pulse Platform background workers...")
    task_ticker = asyncio.create_task(market_ticker_loop())
    task_scanner = asyncio.create_task(scheduled_agent_scan_loop())
    _background_tasks.extend([task_ticker, task_scanner])
    
    # Run initial scan
    await master_orchestrator.run_full_scan()
    yield
    
    logger.info("Shutting down background workers...")
    for t in _background_tasks:
        t.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)


app = FastAPI(
    title="NIFTY-Pulse",
    description="Real-Time Multi-Agent NIFTY50 Intelligence, Quantitative Surveillance & Ephemeris Platform",
    version=config.APP_VERSION,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security & Compliance Headers Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Rate limit check
    if not SecurityGuardrail.check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Please throttle your requests.", "retry_after_sec": 30}
        )

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-SEBI-Compliance"] = "Strict-Non-Advisory-Empirical-Analytics"
    return response


# ==========================================
# Azure Health, Readiness & Compliance Probes
# ==========================================

@app.get("/api/health", response_model=SystemHealth, tags=["System"])
def get_system_health():
    """Azure Container App / App Service Liveness Probe."""
    return SystemHealth(
        status="HEALTHY",
        version=config.APP_VERSION,
        active_agents=6,
        market_data_status="ONLINE",
        rag_engine_status="ONLINE",
        mcp_server_status="READY",
        azure_cloud_region=config.AZURE_REGION,
        sebi_guardrail_status="ENFORCED",
        connected_websockets=alerts_engine.get_connection_count(),
        server_time_utc=datetime.utcnow().isoformat(),
    )


@app.get("/api/ready", tags=["System"])
def get_readiness_probe():
    """Azure Readiness Probe."""
    return {"status": "READY", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/compliance/manifest", tags=["Compliance"])
def get_compliance_manifest():
    """Returns statutory SEBI disclaimer and audit parameters."""
    return ComplianceGuardrail.get_audit_manifest()


# ==========================================
# Market Data Endpoints
# ==========================================

@app.get("/api/market/indices", response_model=MarketIndices, tags=["Market Data"])
def get_market_indices():
    """Returns live NIFTY50, Bank NIFTY, India VIX, GIFT Nifty, and global macro indices."""
    return market_data_service.get_market_indices()


@app.get("/api/market/quotes", response_model=List[StockQuote], tags=["Market Data"])
def get_all_quotes():
    """Returns real-time prices for all 50 constituent companies of NIFTY50."""
    return market_data_service.get_all_quotes()


@app.get("/api/market/quote/{symbol}", response_model=StockQuote, tags=["Market Data"])
def get_stock_quote(symbol: str):
    """Returns detailed real-time quote for a specific ticker."""
    quote = market_data_service.get_stock_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found in NIFTY50 constituents.")
    return quote


@app.get("/api/market/heatmap", tags=["Market Data"])
def get_sector_heatmap():
    """Returns sector-by-sector performance and top gainers/losers."""
    return market_data_service.get_sector_breakdown()


@app.get("/api/market/news", response_model=List[MarketNewsItem], tags=["News Agent"])
def get_market_news(category: Optional[str] = None, limit: int = 20):
    """Returns curated global macro and domestic Indian market news from Agent 1."""
    return market_news_agent.get_latest_news(category=category, limit=limit)


# ==========================================
# Institutional Flow (FII / DII) Endpoints
# ==========================================

@app.get("/api/fii-dii/latest", response_model=FiiDiiRecord, tags=["Institutional Flow Agent"])
def get_latest_fii_dii():
    """Returns the most recent session's FII/DII cash and derivative positioning."""
    return institutional_flow_agent.get_latest_flow_record()


@app.get("/api/fii-dii/history", response_model=List[FiiDiiRecord], tags=["Institutional Flow Agent"])
def get_fii_dii_history(limit: int = 10):
    """Returns historical daily records of FII and DII flows."""
    return institutional_flow_agent.get_historical_flows(limit=limit)


@app.get("/api/fii-dii/summary", tags=["Institutional Flow Agent"])
def get_fii_dii_summary():
    """Returns institutional liquidity summary with F&O Long/Short sentiment meter."""
    return institutional_flow_agent.get_institutional_summary()


# ==========================================
# Leadership & Policy Endpoints
# ==========================================

@app.get("/api/leadership/events", response_model=List[LeadershipEvent], tags=["Leadership Agent"])
def get_leadership_events(leader: Optional[str] = None):
    """Returns monitored events and speeches of PM Modi, FM Sitharaman, and EAM Jaishankar."""
    return leadership_agent.get_latest_events(leader_filter=leader)


# ==========================================
# Conglomerate Radar (Ambani & Adani)
# ==========================================

@app.get("/api/conglomerates/updates", response_model=List[ConglomerateUpdate], tags=["Conglomerate Agent"])
def get_conglomerate_updates(group: Optional[str] = None):
    """Returns strategic capex, JVs, and debt actions for Reliance (Ambani) and Adani groups."""
    return conglomerate_agent.get_latest_updates(group_filter=group)


# ==========================================
# Mega-Asset Managers (BlackRock & Vanguard)
# ==========================================

@app.get("/api/asset-managers/updates", response_model=List[AssetManagerUpdate], tags=["Asset Manager Agent"])
def get_asset_manager_updates(firm: Optional[str] = None):
    """Returns capital commitments, ETF flows (INDA), and weight changes from BlackRock & Vanguard."""
    return asset_manager_agent.get_latest_updates(firm_filter=firm)


# ==========================================
# Quantitative Ephemeris & Cycles (SEBI Compliant)
# ==========================================

@app.get("/api/quantitative/cycles", response_model=List[QuantitativeCycleResult], tags=["Quantitative Ephemeris Agent"])
def get_quantitative_cycles():
    """
    Returns empirical backtest results testing astronomical/ephemeris hypotheses against NIFTY50.
    Includes p-values, t-stats, sample sizes, and statutory non-advisory compliance disclaimers.
    """
    return quant_cycle_agent.get_all_cycle_results()


@app.get("/api/quantitative/cycle/{cycle_type}", response_model=QuantitativeCycleResult, tags=["Quantitative Ephemeris Agent"])
def get_cycle_result(cycle_type: str):
    """Retrieves specific backtest result ('lunar_synodic', 'planetary_retrograde', 'solar_seasonal')."""
    return quant_cycle_agent.get_backtest_result(cycle_type)


# ==========================================
# Real-Time Alerts & Multi-Agent Telemetry
# ==========================================

@app.get("/api/alerts/recent", response_model=List[MarketAlert], tags=["Alerts Engine"])
def get_recent_alerts(
    severity: Optional[SeverityLevel] = None,
    category: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 50,
):
    """Returns structured market alerts with optional severity and ticker filters."""
    return alerts_engine.get_recent_alerts(severity=severity, category=category, symbol=symbol, limit=limit)


@app.get("/api/agents/telemetry", tags=["Multi-Agent Orchestrator"])
def get_agents_telemetry():
    """Returns real-time execution states, composite health score, and agent briefs."""
    return master_orchestrator.get_latest_telemetry()


@app.post("/api/agents/scan", tags=["Multi-Agent Orchestrator"])
async def trigger_manual_scan():
    """Triggers an immediate on-demand full scan across all 6 specialized agents."""
    result = await master_orchestrator.run_full_scan()
    return result


# ==========================================
# RAG (Retrieval-Augmented Generation) Endpoint
# ==========================================

@app.post("/api/rag/query", response_model=RAGQueryResponse, tags=["RAG Engine"])
def query_rag_engine(request: RAGQueryRequest):
    """
    Executes grounded semantic search across official speeches, corporate disclosures,
    and institutional filings with verifiable citations and compliance filters.
    """
    return rag_engine.query(request)


# ==========================================
# MCP (Model Context Protocol) Endpoint
# ==========================================

@app.post("/api/mcp", tags=["MCP Server"])
def handle_mcp_request(request_data: Dict[str, Any]):
    """JSON-RPC 2.0 MCP standard endpoint for AI agent tool execution."""
    return mcp_server.handle_jsonrpc(request_data)


@app.get("/api/mcp/tools", tags=["MCP Server"])
def list_mcp_tools():
    """Returns list of exposed MCP tools."""
    return {"tools": mcp_server.list_tools()}


# ==========================================
# Real-Time WebSocket Streaming Channel
# ==========================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint streaming live NIFTY50 index ticks and real-time market alerts.
    """
    await alerts_engine.connect(websocket)
    try:
        # Send initial snapshot upon connection
        indices = market_data_service.get_market_indices()
        initial_payload = {
            "type": "INITIAL_SNAPSHOT",
            "data": {
                "indices": indices.model_dump(),
                "telemetry": master_orchestrator.get_latest_telemetry(),
                "alerts": [a.model_dump() for a in alerts_engine.get_recent_alerts(limit=10)],
            }
        }
        await websocket.send_json(initial_payload)

        # Keep listening for client ping / heartbeat messages
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        alerts_engine.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket connection error: {e}")
        alerts_engine.disconnect(websocket)


# ==========================================
# Static Files & Dashboard Mount
# ==========================================

# Mount static folder if it exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
    def get_dashboard():
        """Serves the interactive NIFTY-Pulse financial terminal dashboard."""
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), status_code=200)
        return HTMLResponse(content="<h1>NIFTY-Pulse API Running</h1><p>Visit /docs for OpenAPI specs.</p>")
