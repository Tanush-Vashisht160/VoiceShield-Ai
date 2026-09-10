from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContextAssessment:
    """Result of rule-based call-context analysis."""

    score: float
    level: str
    action: str
    reasons: list[str]
    matched_categories: list[str]


class ContextAnalyzer:
    """
    Lightweight rule-based conversation risk analyzer.

    This component does NOT determine whether a voice is AI-generated.
    It evaluates suspicious conversational intent such as:

    - OTP requests
    - banking/payment requests
    - urgency/pressure
    - requests for credentials
    - requests to transfer money
    - callback avoidance
    """

    CATEGORY_PATTERNS = {
        "financial": [
            r"\btransfer\b",
            r"\bsend\s+(?:the\s+)?money\b",
            r"\bpay(?:ment)?\b",
            r"\bbank\s+account\b",
            r"\baccount\s+number\b",
            r"\bupi\b",
            r"\bneft\b",
            r"\bimps\b",
            r"\bcredit\s+card\b",
            r"\bdebit\s+card\b",
        ],
        "otp": [
            r"\botp\b",
            r"\bone[\s-]?time\s+password\b",
            r"\bverification\s+code\b",
            r"\bsecurity\s+code\b",
        ],
        "credentials": [
            r"\bpassword\b",
            r"\bpin\b",
            r"\bpasscode\b",
            r"\bcvv\b",
            r"\bcard\s+details\b",
            r"\blogin\s+details\b",
        ],
        "urgency": [
            r"\burgent\b",
            r"\bimmediately\b",
            r"\bright\s+now\b",
            r"\bas\s+soon\s+as\s+possible\b",
            r"\bwithin\s+\d+\s+(?:minutes?|hours?)\b",
            r"\blast\s+warning\b",
            r"\baccount\s+will\s+be\s+(?:blocked|closed|suspended)\b",
        ],
        "callback_avoidance": [
            r"\bdo\s+not\s+call\s+back\b",
            r"\bdon't\s+call\s+back\b",
            r"\bno\s+need\s+to\s+call\s+back\b",
            r"\bavoid\s+calling\b",
            r"\bcall\s+back\s+later\b",
            r"\bthis\s+number\s+cannot\s+receive\b",
        ],
    }

    CATEGORY_WEIGHTS = {
        "financial": 0.30,
        "otp": 0.30,
        "credentials": 0.25,
        "urgency": 0.15,
        "callback_avoidance": 0.15,
    }

    def analyze(self, text: str) -> dict[str, Any]:
        """
        Analyze conversation text.

        Args:
            text: Transcribed conversation text.

        Returns:
            Dictionary containing risk score, level, action,
            reasons and matched categories.
        """

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        normalized = " ".join(text.lower().split())

        if not normalized:
            return self._build_result(
                score=0.0,
                reasons=[],
                categories=[],
            )

        matched_categories: list[str] = []
        reasons: list[str] = []
        score = 0.0

        for category, patterns in self.CATEGORY_PATTERNS.items():

            matched = any(
                re.search(pattern, normalized)
                for pattern in patterns
            )

            if not matched:
                continue

            matched_categories.append(category)
            score += self.CATEGORY_WEIGHTS[category]

            reasons.append(
                self._reason_for_category(category)
            )

        # Multiple suspicious categories indicate stronger intent.
        if len(matched_categories) >= 3:
            score += 0.10

        elif len(matched_categories) == 2:
            score += 0.05

        score = min(max(score, 0.0), 1.0)

        return self._build_result(
            score=score,
            reasons=reasons,
            categories=matched_categories,
        )

    @staticmethod
    def _reason_for_category(category: str) -> str:

        reasons = {
            "financial":
                "Financial transaction request detected.",

            "otp":
                "OTP or verification-code request detected.",

            "credentials":
                "Sensitive credential request detected.",

            "urgency":
                "Urgency or pressure tactic detected.",

            "callback_avoidance":
                "Callback avoidance behavior detected.",
        }

        return reasons.get(
            category,
            "Suspicious conversation pattern detected.",
        )

    @staticmethod
    def _build_result(
        score: float,
        reasons: list[str],
        categories: list[str],
    ) -> dict[str, Any]:

        if score >= 0.70:
            level = "HIGH"
            action = "BLOCK"

        elif score >= 0.35:
            level = "MEDIUM"
            action = "WARN"

        else:
            level = "LOW"
            action = "ALLOW"

        if not reasons:
            reasons = [
                "No significant conversation risk detected."
            ]

        return {
            "score": round(score, 4),
            "level": level,
            "action": action,
            "reasons": reasons,
            "matched_categories": categories,
        }