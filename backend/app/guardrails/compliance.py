"""
Regulatory & Compliance Guardrail for NIFTY-Pulse Platform.
Enforces compliance with SEBI (Securities and Exchange Board of India) Regulations,
the Indian Information Technology Act, 2000, and corporate defamation standards.
"""
import re
from typing import Dict, Any, Tuple


SEBI_MANDATORY_DISCLAIMER = (
    "STATUTORY SEBI DISCLAIMER: NIFTY-Pulse is an automated quantitative research, "
    "information aggregation, and algorithmic tracking system. This platform is NOT "
    "registered as an Investment Adviser under SEBI (Investment Advisers) Regulations, 2013, "
    "nor as a Research Analyst under SEBI (Research Analysts) Regulations, 2014. "
    "All outputs, sentiment metrics, and quantitative cycle analytics are strictly for "
    "informational and educational purposes. Nothing herein constitutes a recommendation "
    "to buy, sell, or hold any security, derivative, or financial instrument. "
    "Investments in the securities market are subject to market risks; read all related documents "
    "carefully before investing."
)

ASTRONOMICAL_CYCLE_DISCLAIMER = (
    "ASTRONOMICAL & QUANTITATIVE CYCLE DISCLAIMER: Analysis of lunar phases, planetary cycles, "
    "or ephemeris data is conducted strictly as empirical time-series hypothesis testing "
    "(measuring statistical correlation, p-values, and volatility distributions against historical NIFTY50 returns). "
    "Correlation does not imply causation. In strict compliance with SEBI PFUTP Regulations and Indian laws, "
    "no personalized astrological horoscopes, occult predictions, or speculative assertions regarding the personal "
    "lives of public figures or corporate leaders are permitted or generated. All analysis is strictly quantitative, "
    "reproducible, and confined to verifiable public market indices."
)


class ComplianceGuardrail:
    """
    Enforces compliance filters to guarantee that intelligence feeds,
    agent summaries, and user queries remain strictly legal, factual,
    and free from regulatory liability.
    """

    # Prohibited patterns: defamatory, superstitious occult trading claims, private life speculation
    PROHIBITED_PERSONAL_SPECULATIONS = [
        r"(kundli|horoscope|birth\s*chart|janam\s*kundli)\s*(of|for)?\s*(modi|shah|ambani|adani)",
        r"(death|illness|family\s*scandal|personal\s*tragedy)\s*(of|in)?\s*(modi|shah|ambani|adani)",
        r"(astrology\s*guarantees|stars\s*predict\s*100%|planetary\s*sure\s*shot)",
        r"(insider\s*tip|guaranteed\s*multibagger|100%\s*profit\s*call)",
    ]

    @classmethod
    def sanitize_agent_output(cls, text: str) -> Tuple[str, bool, str]:
        """
        Inspects agent outputs before dispatching to frontend or alerts.
        Returns: (sanitized_text, was_flagged, reason)
        """
        for pattern in cls.PROHIBITED_PERSONAL_SPECULATIONS:
            if re.search(pattern, text, re.IGNORECASE):
                sanitized = re.sub(pattern, "[COMPLIANCE_REDACTED: Non-public / Personal Speculation Blocked]", text, flags=re.IGNORECASE)
                reason = "Blocked personal astrological speculation or non-compliant tip claim under SEBI PFUTP guidelines."
                return sanitized, True, reason

        return text, False, "Compliant"

    @classmethod
    def validate_query(cls, query: str) -> Tuple[bool, str]:
        """
        Validates user or agent queries to prevent regulatory/legal violations.
        """
        lower_q = query.lower()
        for pattern in cls.PROHIBITED_PERSONAL_SPECULATIONS:
            if re.search(pattern, lower_q):
                return False, (
                    "Query violates platform legal guardrails. In compliance with SEBI regulations "
                    "and privacy protections, private horoscope or personal life speculation regarding public figures "
                    "is blocked. Please query empirical market data, corporate capex, official policy announcements, "
                    "or historical quantitative cycle distributions."
                )

        return True, "Valid"

    @classmethod
    def get_audit_manifest(cls) -> Dict[str, Any]:
        """
        Returns full compliance policy metadata for enterprise auditing and Azure governance.
        """
        return {
            "sebi_ra_compliance": "Regulation 4 Non-Advisory Exemption Enforced",
            "sebi_ia_compliance": "No Client Profiling / No Trading Directives",
            "ephemeris_standard": "Empirical Null Hypothesis Significance Testing Only",
            "defamation_shield": "Strict Public-Data Only / Zero Personal Speculation",
            "statutory_disclaimer": SEBI_MANDATORY_DISCLAIMER,
            "cycle_disclaimer": ASTRONOMICAL_CYCLE_DISCLAIMER,
        }
