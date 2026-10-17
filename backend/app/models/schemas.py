"""
Pydantic Schemas for NIFTY-Pulse Platform
Data contracts for stocks, agents, market intelligence, quantitative cycles, and alerts.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class SentimentType(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class StockQuote(BaseModel):
    symbol: str = Field(..., description="NSE Ticker Symbol, e.g. RELIANCE, TCS")
    name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Primary Sector (IT, Banking, Oil & Gas, etc.)")
    price: float = Field(..., description="Current/Last Traded Price in INR")
    change: float = Field(..., description="Absolute change in INR")
    change_percent: float = Field(..., description="Percentage change")
    day_high: float = Field(..., description="Intraday high")
    day_low: float = Field(..., description="Intraday low")
    volume: int = Field(default=0, description="Volume traded")
    market_cap_cr: float = Field(default=0.0, description="Market Capitalization in Crores")
    pe_ratio: Optional[float] = Field(default=None, description="P/E Ratio")
    year_high: float = Field(default=0.0, description="52 Week High")
    year_low: float = Field(default=0.0, description="52 Week Low")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MarketIndices(BaseModel):
    nifty50_price: float
    nifty50_change: float
    nifty50_change_percent: float
    banknifty_price: float
    banknifty_change: float
    banknifty_change_percent: float
    india_vix: float
    india_vix_change: float
    gift_nifty: float
    gift_nifty_change: float
    brent_crude_usd: float
    us_dollar_inr: float
    us_10y_yield: float
    advances: int = Field(default=0, description="NIFTY50 advancing stocks")
    declines: int = Field(default=0, description="NIFTY50 declining stocks")
    unchanged: int = Field(default=0, description="NIFTY50 unchanged stocks")
    market_status: str = Field(default="OPEN", description="OPEN, CLOSED, or PRE-OPEN")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class FiiDiiRecord(BaseModel):
    date: str
    fii_cash_buy: float
    fii_cash_sell: float
    fii_cash_net: float = Field(..., description="Net FII Cash flow in INR Crores")
    dii_cash_buy: float
    dii_cash_sell: float
    dii_cash_net: float = Field(..., description="Net DII Cash flow in INR Crores")
    fii_index_futures_long: int = Field(default=0, description="Contracts long")
    fii_index_futures_short: int = Field(default=0, description="Contracts short")
    fii_long_short_ratio: float = Field(default=0.5, description="FII Index Futures Long/(Long+Short)")
    dii_net_cumulative_month: float = Field(default=0.0, description="DII MTD flow in Crores")
    fii_net_cumulative_month: float = Field(default=0.0, description="FII MTD flow in Crores")
    sentiment: SentimentType = Field(default=SentimentType.NEUTRAL)
    institutional_signal: str = Field(default="NEUTRAL ACCUMULATION")


class MarketNewsItem(BaseModel):
    id: str
    headline: str
    summary: str
    source: str
    category: str = Field(..., description="GLOBAL_MACRO, DOMESTIC_MACRO, REGULATORY_SEBI, EARNINGS")
    impact_score: float = Field(..., description="-1.0 (Very Bearish) to +1.0 (Very Bullish)")
    sentiment: SentimentType
    affected_tickers: List[str] = Field(default_factory=list)
    affected_sectors: List[str] = Field(default_factory=list)
    published_at: str
    url: Optional[str] = None


class LeadershipEvent(BaseModel):
    id: str
    leader_name: str = Field(..., description="PM Narendra Modi, FM Nirmala Sitharaman, or EAM S. Jaishankar")
    designation: str
    event_type: str = Field(..., description="SPEECH, BILATERAL_SUMMIT, BUDGET_POLICY, CABINET_DECISION, DIPLOMATIC_TRADE")
    headline: str
    key_themes: List[str] = Field(default_factory=list, description="e.g. Semiconductors, Defense, Capex, Middle East Corridor")
    impacted_sectors: List[str] = Field(default_factory=list)
    summary: str
    policy_significance: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    market_sentiment: SentimentType = Field(default=SentimentType.BULLISH)
    source_attribution: str = Field(default="PIB / PMO / MEA Official Release")
    timestamp: str


class ConglomerateUpdate(BaseModel):
    id: str
    group_name: str = Field(..., description="Reliance Industries (Ambani) or Adani Group")
    key_entities: List[str] = Field(..., description="e.g. RELIANCE, JIO, ADANIENT, ADANIPORTS")
    headline: str
    category: str = Field(..., description="CAPEX, JOINT_VENTURE, DEBT_REFINANCING, GREEN_ENERGY, REGULATORY")
    summary: str
    sentiment: SentimentType
    impact_severity: SeverityLevel
    strategic_details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class AssetManagerUpdate(BaseModel):
    id: str
    institution_name: str = Field(..., description="BlackRock or Vanguard")
    entity_tracked: str = Field(..., description="Larry Fink Commentary, iShares MSCI India ETF (INDA), Vanguard Emerging Markets")
    update_type: str = Field(..., description="PORTFOLIO_WEIGHT, ETF_FLOW, STRATEGIC_ALLIANCE, COMMENTARY")
    headline: str
    summary: str
    estimated_flow_usd_mn: Optional[float] = None
    affected_tickers: List[str] = Field(default_factory=list)
    sentiment: SentimentType
    timestamp: str


class QuantitativeCycleResult(BaseModel):
    cycle_name: str = Field(..., description="Lunar Synodic Cycle, Solar Seasonal Cycle, Planetary Retrograde Window")
    target_metric: str = Field(default="NIFTY50 Daily Return & Volatility")
    hypothesis: str
    historical_periods_tested: int
    win_rate_percent: float
    mean_return_during_phase: float = Field(..., description="Average daily return in %")
    mean_return_benchmark: float = Field(..., description="Baseline average return in %")
    volatility_during_phase: float = Field(..., description="Annualized volatility in %")
    volatility_benchmark: float = Field(..., description="Baseline annualized volatility in %")
    t_statistic: float
    p_value: float = Field(..., description="Student's t-test / permutation p-value")
    statistically_significant_at_95: bool
    empirical_conclusion: str
    active_current_state: str = Field(..., description="e.g. 'Waxing Gibbous', 'Mercury Direct'")
    sebi_compliance_note: str = Field(
        default="Purely quantitative empirical cycle backtest. Not SEBI registered investment advice. Correlation does not imply causation."
    )


class MarketAlert(BaseModel):
    id: str
    title: str
    severity: SeverityLevel
    category: str = Field(..., description="FII_SURGE, POLICY_BREAKTHROUGH, CONGLOMERATE_ACTION, GLOBAL_MACRO, VOLATILITY")
    sentiment: SentimentType
    affected_symbols: List[str] = Field(default_factory=list)
    message: str
    actionable_insight: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgentStatus(BaseModel):
    agent_id: str
    name: str
    role: str
    state: str = Field(default="IDLE", description="IDLE, SCANNING, ANALYZING, COMPLETED, ERROR")
    last_run_time: str
    execution_time_ms: int = Field(default=0)
    findings_count: int = Field(default=0)
    latest_brief: str
    health: str = Field(default="HEALTHY")


class SystemHealth(BaseModel):
    status: str = "HEALTHY"
    version: str = "1.0.0"
    active_agents: int = 6
    market_data_status: str = "ONLINE"
    rag_engine_status: str = "ONLINE"
    mcp_server_status: str = "READY"
    azure_cloud_region: str = "centralindia"
    sebi_guardrail_status: str = "ENFORCED"
    connected_websockets: int = 0
    server_time_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="User question or research query")
    filter_category: Optional[str] = None
    top_k: int = Field(default=4, ge=1, le=10)


class RAGDocumentCitation(BaseModel):
    doc_id: str
    title: str
    category: str
    source: str
    snippet: str
    relevance_score: float
    date: str


class RAGQueryResponse(BaseModel):
    query: str
    synthesized_answer: str
    citations: List[RAGDocumentCitation]
    confidence_score: float
    compliance_disclaimer: str
