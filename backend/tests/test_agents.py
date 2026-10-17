"""
Unit and integration tests for NIFTY-Pulse specialized agents.
"""
import pytest
from backend.app.agents.news_agent import market_news_agent
from backend.app.agents.fii_dii_agent import institutional_flow_agent
from backend.app.agents.leadership_agent import leadership_agent
from backend.app.agents.conglomerate_agent import conglomerate_agent
from backend.app.agents.asset_manager_agent import asset_manager_agent
from backend.app.agents.quantitative_cycle_agent import quant_cycle_agent
from backend.app.agents.orchestrator import master_orchestrator


def test_market_news_agent():
    news = market_news_agent.get_latest_news()
    assert len(news) > 0
    assert news[0].headline is not None
    assert -1.0 <= news[0].impact_score <= 1.0
    status = market_news_agent.scan_news()
    assert status.health == "HEALTHY"


def test_fii_dii_agent():
    record = institutional_flow_agent.get_latest_flow_record()
    assert record.date is not None
    assert isinstance(record.fii_cash_net, float)
    assert isinstance(record.dii_cash_net, float)
    assert 0.0 <= record.fii_long_short_ratio <= 1.0


def test_leadership_agent():
    events = leadership_agent.get_latest_events()
    assert len(events) >= 3
    leaders = [e.leader_name for e in events]
    assert any("Modi" in l for l in leaders)
    assert any("Sitharaman" in l for l in leaders)
    assert any("Jaishankar" in l for l in leaders)


def test_conglomerate_agent():
    updates = conglomerate_agent.get_latest_updates()
    assert len(updates) >= 3
    groups = [u.group_name for u in updates]
    assert any("Reliance" in g for g in groups)
    assert any("Adani" in g for g in groups)


def test_asset_manager_agent():
    updates = asset_manager_agent.get_latest_updates()
    assert len(updates) >= 2
    firms = [u.institution_name for u in updates]
    assert "BlackRock" in firms
    assert "Vanguard" in firms


def test_quantitative_cycle_agent():
    cycles = quant_cycle_agent.get_all_cycle_results()
    assert len(cycles) >= 3
    for c in cycles:
        assert c.p_value >= 0.05
        assert c.statistically_significant_at_95 is False
        assert "SEBI" in c.sebi_compliance_note or "PFUTP" in c.sebi_compliance_note
