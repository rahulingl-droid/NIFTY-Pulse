"""Agents package initialization."""
from backend.app.agents.news_agent import market_news_agent, MarketNewsAgent
from backend.app.agents.fii_dii_agent import institutional_flow_agent, InstitutionalFlowAgent
from backend.app.agents.leadership_agent import leadership_agent, NationalLeadershipAgent
from backend.app.agents.conglomerate_agent import conglomerate_agent, ConglomerateRadarAgent
from backend.app.agents.asset_manager_agent import asset_manager_agent, MegaAssetManagerAgent
from backend.app.agents.quantitative_cycle_agent import quant_cycle_agent, QuantitativeCycleAgent
from backend.app.agents.orchestrator import master_orchestrator, MasterOrchestrator

__all__ = [
    "market_news_agent",
    "MarketNewsAgent",
    "institutional_flow_agent",
    "InstitutionalFlowAgent",
    "leadership_agent",
    "NationalLeadershipAgent",
    "conglomerate_agent",
    "ConglomerateRadarAgent",
    "asset_manager_agent",
    "MegaAssetManagerAgent",
    "quant_cycle_agent",
    "QuantitativeCycleAgent",
    "master_orchestrator",
    "MasterOrchestrator",
]
