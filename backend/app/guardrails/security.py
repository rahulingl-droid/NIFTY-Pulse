"""
Security and Defensive Guardrails for NIFTY-Pulse.
Includes prompt injection detection, PII scrubbing, input sanitization, and rate limiting.
"""
import re
import time
from typing import Tuple, Dict, List
from collections import defaultdict


class SecurityGuardrail:
    """
    Protects multi-agent pipeline and RAG systems against malicious inputs,
    prompt injection, and data leakages.
    """

    # Prompt injection signatures
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"system\s*prompt",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"jailbreak",
        r"reveal\s+your\s+(api\s*key|internal\s*instructions|rules|secret)",
        r"<script.*?>.*?</script>",
        r"DROP\s+TABLE|SELECT\s+\*\s+FROM|UNION\s+SELECT",
    ]

    # PII patterns (Indian context: PAN, Indian Phone numbers, Aadhaar)
    PII_PATTERNS = [
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
        (r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", "[REDACTED_PAN]"),  # Permanent Account Number
        (r"(?:\+91[-.\s]?)?[6-9]\d{9}\b", "[REDACTED_PHONE]"),  # Indian Mobile (10 digits starting with 6-9)
        (r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b", "[REDACTED_AADHAAR]"),  # Aadhaar 12 digits formatted
        (r"\b[2-9]\d{11}\b", "[REDACTED_AADHAAR]"),  # Aadhaar 12 digits unformatted
    ]

    # Simple In-Memory Rate Limiter: IP -> list of timestamps
    _rate_limits: Dict[str, List[float]] = defaultdict(list)
    RATE_LIMIT_WINDOW_SEC = 60
    MAX_REQUESTS_PER_WINDOW = 120

    @classmethod
    def check_prompt_injection(cls, user_text: str) -> Tuple[bool, str]:
        """
        Detects prompt injection or adversarial inputs.
        Returns: (is_safe, message)
        """
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, user_text, re.IGNORECASE):
                return False, f"Malicious input pattern detected ({pattern}). Request blocked by Security Guardrail."
        return True, "Safe"

    @classmethod
    def scrub_pii(cls, text: str) -> str:
        """
        Scrubs personally identifiable information (Aadhaar, PAN, phone numbers).
        """
        scrubbed = text
        for pattern, replacement in cls.PII_PATTERNS:
            scrubbed = re.sub(pattern, replacement, scrubbed)
        return scrubbed

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """
        Strips dangerous HTML/script tags and normalizes whitespace.
        """
        clean = re.sub(r"<[^>]*>", "", text)
        return clean.strip()

    @classmethod
    def check_rate_limit(cls, client_ip: str) -> bool:
        """
        Rate limiter allowing up to MAX_REQUESTS_PER_WINDOW per minute per client IP.
        """
        now = time.time()
        timestamps = cls._rate_limits[client_ip]
        # Keep only recent timestamps
        cls._rate_limits[client_ip] = [ts for ts in timestamps if now - ts < cls.RATE_LIMIT_WINDOW_SEC]
        
        if len(cls._rate_limits[client_ip]) >= cls.MAX_REQUESTS_PER_WINDOW:
            return False
            
        cls._rate_limits[client_ip].append(now)
        return True
