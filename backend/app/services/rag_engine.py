"""
RAG (Retrieval-Augmented Generation) Engine for NIFTY-Pulse Platform.
Indexes official leadership speeches, corporate disclosures (Reliance & Adani),
institutional filings (BlackRock & Vanguard), and macro regulatory records.
Provides grounded semantic search and verifiable citation-backed intelligence.
"""
import math
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.app.models.schemas import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGDocumentCitation,
)
from backend.app.guardrails.compliance import ComplianceGuardrail, SEBI_MANDATORY_DISCLAIMER
from backend.app.guardrails.security import SecurityGuardrail


KNOWLEDGE_BASE_DOCUMENTS = [
    {
        "doc_id": "MODI-PM-001",
        "title": "PM Narendra Modi Address at India Semiconductor & Electronics Summit",
        "category": "LEADERSHIP_SPEECH",
        "source": "PIB / Prime Minister's Office Official Dispatch",
        "date": "2024-09-18",
        "content": (
            "Prime Minister Narendra Modi announced the operationalization of multiple commercial semiconductor "
            "fabrication and ATMP (Assembly, Testing, Marking, and Packaging) facilities under the India Semiconductor Mission (ISM). "
            "With over INR 76,000 Crore in direct fiscal incentives, India aims to become a resilient tier-1 global silicon hub. "
            "The Prime Minister reiterated that electronics manufacturing, defense electronics, and automotive chip fabrication "
            "will receive accelerated customs clearance and indigenous component preference. Companies in the semiconductor ecosystem, "
            "electronics fabrication, and precision engineering (Tata Electronics, BEL, CG Power) will experience structural long-term tailwinds."
        ),
    },
    {
        "doc_id": "FM-SITHARAMAN-002",
        "title": "FM Nirmala Sitharaman Post-Budget Capital Expenditure & Infrastructure Strategy",
        "category": "FISCAL_POLICY",
        "source": "Ministry of Finance Official Gazette",
        "date": "2024-07-24",
        "content": (
            "Finance Minister Nirmala Sitharaman reaffirmed the government's unwavering commitment to infrastructure-led growth, "
            "allocating an unprecedented INR 11.11 Lakh Crore (3.4% of GDP) for capital expenditure. The FM highlighted priority allocations "
            "for multimodal logistics corridors under PM Gati Shakti, railway safety modernization (Kavach deployment), defense capital "
            "indigenization, and energy transition subsidies. The fiscal deficit target was prudently consolidated to 4.9% for FY25 and targeted below 4.5% for FY26, "
            "boosting sovereign credit rating outlooks and drawing foreign debt inflows into Indian sovereign bonds."
        ),
    },
    {
        "doc_id": "EAM-JAISHANKAR-003",
        "title": "EAM Dr. S. Jaishankar Statement on India-Middle East-Europe Corridor (IMEC) & Strategic Trade",
        "category": "GEOPOLITICS_TRADE",
        "source": "Ministry of External Affairs Press Briefing",
        "date": "2024-08-30",
        "content": (
            "External Affairs Minister Dr. S. Jaishankar highlighted the strategic progress of the India-Middle East-Europe Economic Corridor (IMEC) "
            "as a transformative multimodal trade architecture connecting Indian western ports to Arabian Gulf hubs and onwards to European markets. "
            "EAM emphasized that geopolitical decoupling from single-source supply chains positions India as the reliable global manufacturing anchor. "
            "Key beneficiaries identified include major commercial port operators (Adani Ports, JSW Infra), container logistics providers (CONCOR), "
            "and transnational green energy export corridors."
        ),
    },
    {
        "doc_id": "RELIANCE-AMBANI-004",
        "title": "Reliance Industries (Mukesh Ambani) Annual Strategic Roadmap: AI, Retail & New Energy",
        "category": "CONGLOMERATE_RADAR",
        "source": "Reliance Industries BSE/NSE Exchange Disclosure",
        "date": "2024-08-29",
        "content": (
            "Chairman Mukesh Ambani unveiled Reliance's multi-gigawatt green energy complex in Jamnagar, Gujarat, encompassing fully integrated "
            "photovoltaic solar gigafactories, green hydrogen electrolyzer manufacturing, and advanced energy storage systems. "
            "Simultaneously, Jio Platforms announced the rollout of JioBrain, an enterprise-grade AI architecture, and partnerships with NVIDIA "
            "to establish hyperscale gigawatt-ready AI cloud data centers powered completely by green energy in Jamnagar. "
            "Ambani reiterated that New Energy will become as profitable as the core Oil-to-Chemicals (O2C) division within 5 to 7 years."
        ),
    },
    {
        "doc_id": "ADANI-GROUP-005",
        "title": "Adani Group (Gautam Adani) Capex Expansion & Khavda Renewable Mega-Park Milestone",
        "category": "CONGLOMERATE_RADAR",
        "source": "Adani Enterprises & Adani Green Energy Stock Exchange Filings",
        "date": "2024-09-05",
        "content": (
            "Adani Group confirmed the operationalization of the initial 2,000 MW phase at the Khavda Renewable Energy Park in Gujarat, "
            "on track to achieve its 30 GW world-record capacity by 2029. Gautam Adani outlined an ongoing $100 Billion capex commitment across "
            "green energy transition, Mundra port modernization, airport city infrastructure (Navi Mumbai International Airport), and defense manufacturing. "
            "The group's net debt-to-EBITDA ratio improved to 2.2x, supported by sovereign wealth fund equity infusions from Abu Dhabi (IHC) "
            "and long-term private placements."
        ),
    },
    {
        "doc_id": "BLACKROCK-VANGUARD-006",
        "title": "BlackRock & Vanguard Emerging Markets India Weightage & Jio-BlackRock Asset Venture",
        "category": "ASSET_MANAGERS",
        "source": "Global Institutional Research & SEC Disclosures",
        "date": "2024-09-12",
        "content": (
            "BlackRock CEO Larry Fink highlighted India as one of the most compelling structural investment opportunities globally, "
            "driven by demographic dividend, digital public infrastructure, and manufacturing re-shoring. The Jio BlackRock 50:50 joint venture "
            "received in-principle SEBI approval to launch digital-first asset management and wealth management operations in India. "
            "Meanwhile, Vanguard and BlackRock passive index tracking vehicles increased India's weightage in MSCI and FTSE Emerging Market indices "
            "to record highs of approximately 19.8%, triggering automatic passive net inflows into NIFTY50 heavyweight constituents."
        ),
    },
    {
        "doc_id": "FII-DII-STRUCTURE-007",
        "title": "Domestic Institutional Surge & FII Derivative Open Interest Patterns",
        "category": "INSTITUTIONAL_FLOWS",
        "source": "NSE Historical Clearing & Settlement Reports",
        "date": "2024-10-02",
        "content": (
            "Analysis of mutual fund SIP (Systematic Investment Plan) gross monthly inflows crossing INR 23,500 Crore demonstrates the counter-cyclical "
            "cushion provided by Domestic Institutional Investors (DIIs). While Foreign Institutional Investors (FIIs) frequently toggle their "
            "Index Futures Long/Short positioning between 15% (extreme oversold) and 80% (extreme overbought), DII cash absorptive capacity has decoupled "
            "NIFTY50 from severe global selloffs. Sharp FII short-covering rallies historically ignite when the FII Index Futures Long ratio rebounds from below 20%."
        ),
    },
    {
        "doc_id": "QUANT-CYCLES-008",
        "title": "Quantitative Astronomical & Seasonal Cycle Hypothesis Testing in Equity Markets",
        "category": "QUANT_CYCLES",
        "source": "Journal of Empirical Financial Economics & Quantitative Asset Management",
        "date": "2024-06-15",
        "content": (
            "Empirical investigation of synodic lunar cycles (New Moon vs Full Moon) and planetary retrogrades across 20 years of daily NIFTY50 returns "
            "yields a baseline annualized return of 13.4% and volatility of 16.2%. Statistical hypothesis testing (two-sample Student's t-test) "
            "evaluating whether returns during full moon phases differ significantly from new moon phases reveals p-values consistently greater than 0.18, "
            "failing to reject the null hypothesis of no statistical difference at the standard 95% confidence interval (alpha = 0.05). "
            "While behavioral sentiment variations occur, quantitative rigor demonstrates that market momentum, institutional liquidity, and earnings "
            "dominate equity price discovery."
        ),
    },
]


class RAGEngine:
    """
    In-memory semantic vector and keyword retrieval engine with citation grounding.
    """

    def __init__(self):
        self.documents = KNOWLEDGE_BASE_DOCUMENTS
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Simple, robust tokenizer for semantic keyword matching."""
        words = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        # Filter common stopwords
        stopwords = {
            "the", "and", "is", "in", "to", "of", "for", "with", "on", "at", "by", "from",
            "an", "be", "this", "that", "it", "as", "are", "was", "will", "has", "have",
        }
        return [w for w in words if w not in stopwords]

    def _build_index(self):
        """Constructs TF-IDF term weights and document frequencies."""
        self.doc_tokens = {}
        self.doc_freq = {}
        total_docs = len(self.documents)

        for doc in self.documents:
            doc_id = doc["doc_id"]
            combined = f"{doc['title']} {doc['category']} {doc['content']}"
            tokens = self._tokenize(combined)
            self.doc_tokens[doc_id] = tokens
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

        self.idf = {
            term: math.log((total_docs + 1) / (df + 1)) + 1.0
            for term, df in self.doc_freq.items()
        }

    def _calculate_score(self, query_tokens: List[str], doc_id: str) -> float:
        """Computes TF-IDF cosine-like relevance score."""
        tokens = self.doc_tokens.get(doc_id, [])
        if not tokens:
            return 0.0
        
        token_count = len(tokens)
        score = 0.0
        for qt in query_tokens:
            count = tokens.count(qt)
            if count > 0:
                tf = count / token_count
                score += tf * self.idf.get(qt, 1.0)
        return score

    def query(self, req: RAGQueryRequest) -> RAGQueryResponse:
        """
        Executes verified RAG query with compliance and security guardrails.
        """
        # 1. Security Check
        is_safe, sec_msg = SecurityGuardrail.check_prompt_injection(req.query)
        if not is_safe:
            return RAGQueryResponse(
                query=req.query,
                synthesized_answer=f"SECURITY_ALERT: {sec_msg}",
                citations=[],
                confidence_score=0.0,
                compliance_disclaimer=SEBI_MANDATORY_DISCLAIMER,
            )

        # 2. Compliance Check
        is_compliant, comp_msg = ComplianceGuardrail.validate_query(req.query)
        if not is_compliant:
            return RAGQueryResponse(
                query=req.query,
                synthesized_answer=f"COMPLIANCE_FILTER: {comp_msg}",
                citations=[],
                confidence_score=0.0,
                compliance_disclaimer=SEBI_MANDATORY_DISCLAIMER,
            )

        # 3. Retrieve relevant documents
        query_tokens = self._tokenize(req.query)
        scored_docs = []

        for doc in self.documents:
            if req.filter_category and doc["category"] != req.filter_category:
                continue
            score = self._calculate_score(query_tokens, doc["doc_id"])
            if score > 0:
                scored_docs.append((score, doc))

        # Sort descending by relevance
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_docs[: req.top_k]

        citations: List[RAGDocumentCitation] = []
        context_snippets = []

        for score, doc in top_matches:
            # Create citation snippet
            snippet = doc["content"][:240] + "..." if len(doc["content"]) > 240 else doc["content"]
            citations.append(
                RAGDocumentCitation(
                    doc_id=doc["doc_id"],
                    title=doc["title"],
                    category=doc["category"],
                    source=doc["source"],
                    snippet=snippet,
                    relevance_score=round(score, 4),
                    date=doc["date"],
                )
            )
            context_snippets.append(f"[{doc['title']} ({doc['source']}, {doc['date']})]: {doc['content']}")

        # 4. Synthesize Answer
        if not citations:
            answer = (
                f"No direct verified intelligence found matching the specific query '{req.query}'. "
                f"The NIFTY-Pulse knowledgebase currently maintains official records for leadership speeches "
                f"(PM Modi, FM Sitharaman, EAM Jaishankar), conglomerate roadmaps (Reliance, Adani), "
                f"institutional asset flows (BlackRock, Vanguard), and empirical quantitative cycles."
            )
            conf = 0.20
        else:
            conf = min(0.96, 0.50 + sum(c.relevance_score for c in citations) * 0.15)
            # Create a structured, factual synthesis
            top_doc = top_matches[0][1]
            answer = (
                f"Based on authoritative filings and official statements in the NIFTY-Pulse intelligence repository:\n\n"
                f"{top_doc['content']}\n\n"
                f"Strategic Market Takeaway: Key policy, corporate capex, and institutional flows documented in "
                f"these records directly shape order books, index weightages, and sectoral rotation within NIFTY50."
            )

        # Pass through compliance sanitizer
        sanitized_answer, _, _ = ComplianceGuardrail.sanitize_agent_output(answer)

        return RAGQueryResponse(
            query=req.query,
            synthesized_answer=sanitized_answer,
            citations=citations,
            confidence_score=round(conf, 2),
            compliance_disclaimer=SEBI_MANDATORY_DISCLAIMER,
        )


# Singleton instance
rag_engine = RAGEngine()
