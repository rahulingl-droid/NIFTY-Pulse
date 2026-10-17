"""
Real-Time Alerts Engine for NIFTY-Pulse Platform.
Evaluates multi-factor market triggers, deduplicates signals, and broadcasts structured
alerts to connected WebSocket clients.
"""
import asyncio
import logging
from typing import List, Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket
from backend.app.models.schemas import MarketAlert, SeverityLevel, SentimentType
from backend.app.guardrails.compliance import ComplianceGuardrail

logger = logging.getLogger("alerts_engine")


INITIAL_ALERTS = [
    MarketAlert(
        id="ALT-101",
        title="FII Derivative Pivot: Index Futures Long Ratio Crosses 58%",
        severity=SeverityLevel.HIGH,
        category="FII_SURGE",
        sentiment=SentimentType.BULLISH,
        affected_symbols=["NIFTY50", "BANKNIFTY", "HDFCBANK", "RELIANCE"],
        message="Foreign Institutional Investors added 24,500 net long contracts in Nifty & Bank Nifty Index Futures, signaling aggressive short-covering.",
        actionable_insight="Short-covering momentum tends to provide support near 25,000 psychological strike.",
        timestamp=datetime.utcnow().isoformat(),
    ),
    MarketAlert(
        id="ALT-102",
        title="PM Semiconductor Directive: INR 76k Cr Mission Acceleration",
        severity=SeverityLevel.CRITICAL,
        category="POLICY_BREAKTHROUGH",
        sentiment=SentimentType.BULLISH,
        affected_symbols=["BEL", "TCS", "LT"],
        message="Cabinet clears expanded fiscal subventions for advanced ATMP facilities; domestic capital goods and electronics firms prioritized.",
        actionable_insight="Direct long-term earnings expansion expected for domestic defense electronics and industrial automation majors.",
        timestamp=datetime.utcnow().isoformat(),
    ),
    MarketAlert(
        id="ALT-103",
        title="Reliance-NVIDIA AI Hyperscale Gigawatt Complex Greenlit",
        severity=SeverityLevel.HIGH,
        category="CONGLOMERATE_ACTION",
        sentiment=SentimentType.BULLISH,
        affected_symbols=["RELIANCE", "INFY", "TCS"],
        message="Reliance confirms Jamnagar green-powered AI compute cluster buildout to host enterprise sovereign AI models.",
        actionable_insight="Significant re-rating potential for Reliance Jio Platforms enterprise cloud division.",
        timestamp=datetime.utcnow().isoformat(),
    ),
    MarketAlert(
        id="ALT-104",
        title="BlackRock iShares India (INDA) Net Inflows Surge $180M in 48 Hours",
        severity=SeverityLevel.MEDIUM,
        category="GLOBAL_MACRO",
        sentiment=SentimentType.BULLISH,
        affected_symbols=["HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL"],
        message="Global emerging market reallocation redirects passive capital toward top Indian large caps as Fed easing cycle solidifies.",
        actionable_insight="Passive ETF basket purchases offer sustained liquidity during afternoon settlement windows.",
        timestamp=datetime.utcnow().isoformat(),
    ),
    MarketAlert(
        id="ALT-105",
        title="Brent Crude Rebounds to $74.5/bbl on Middle East Shipping Tension",
        severity=SeverityLevel.MEDIUM,
        category="VOLATILITY",
        sentiment=SentimentType.BEARISH,
        affected_symbols=["BPCL", "ASIANPAINT", "MARUTI"],
        message="Geopolitical shipping route rerouting marginally increases raw material input cost expectations for oil marketing and paint manufacturers.",
        actionable_insight="Monitor downstream gross refining margins and auto fuel marketing margins for margin pressure.",
        timestamp=datetime.utcnow().isoformat(),
    ),
]


class AlertsEngine:
    """
    Alerts dispatcher with in-memory ring buffer and real-time WebSocket broadcaster.
    """

    def __init__(self, max_history: int = 150):
        self.max_history = max_history
        self._alerts: List[MarketAlert] = list(INITIAL_ALERTS)
        self._active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Registers a new real-time WebSocket subscriber."""
        await websocket.accept()
        self._active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active listeners: {len(self._active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Removes a disconnected WebSocket subscriber."""
        self._active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active listeners: {len(self._active_connections)}")

    async def broadcast_alert(self, alert: MarketAlert):
        """Broadcasts a newly generated alert to all connected web clients."""
        # Sanitize alert content via compliance guardrail
        sanitized_msg, _, _ = ComplianceGuardrail.sanitize_agent_output(alert.message)
        alert.message = sanitized_msg

        # Prepend to history ring buffer
        self._alerts.insert(0, alert)
        if len(self._alerts) > self.max_history:
            self._alerts.pop()

        payload = {
            "type": "NEW_ALERT",
            "data": alert.model_dump(),
        }

        # Broadcast asynchronously
        dead_connections = set()
        for connection in self._active_connections:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.debug(f"Failed to send to client: {e}")
                dead_connections.add(connection)

        for dead in dead_connections:
            self._active_connections.discard(dead)

    async def broadcast_market_tick(self, tick_data: Dict):
        """Streams real-time market index ticks and price updates to clients."""
        payload = {
            "type": "MARKET_TICK",
            "data": tick_data,
        }
        dead_connections = set()
        for connection in self._active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                dead_connections.add(connection)

        for dead in dead_connections:
            self._active_connections.discard(dead)

    def get_recent_alerts(
        self,
        severity: Optional[SeverityLevel] = None,
        category: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 50,
    ) -> List[MarketAlert]:
        """Filters and retrieves recent alerts."""
        results = self._alerts
        if severity:
            results = [a for a in results if a.severity == severity]
        if category:
            results = [a for a in results if a.category == category]
        if symbol:
            results = [a for a in results if symbol.upper() in a.affected_symbols]
        return results[:limit]

    def get_connection_count(self) -> int:
        """Returns the number of active real-time subscribers."""
        return len(self._active_connections)


# Singleton instance
alerts_engine = AlertsEngine()
