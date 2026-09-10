from __future__ import annotations

import re
from typing import Any

from app.intent_analyzer import IntentAnalyzer


class ContextAnalyzer:
    """
    Dynamic conversation-context risk analyzer.

    ContextAnalyzer answers:

        "How suspicious is the conversation?"

    IntentAnalyzer answers:

        "What is the caller trying to make the victim do?"

    The two analyses are intentionally separated.

    Context risk is calculated from actual evidence present in
    the transcript instead of simply adding fixed category weights.
    """

    SIGNAL_PATTERNS = {
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
            r"\bgift\s+card\b",
            r"\bvoucher\b",
            r"\bcrypto(?:currency)?\b",
        ],

        "credential_request": [
            r"\bpassword\b",
            r"\bpin\b",
            r"\bpasscode\b",
            r"\bcvv\b",
            r"\bcard\s+details\b",
            r"\blogin\s+details\b",
            r"\bcredentials\b",
            r"\bsecurity\s+question\b",
        ],

        "otp_request": [
            r"\botp\b",
            r"\bone[\s-]?time\s+password\b",
            r"\bverification\s+code\b",
            r"\bsecurity\s+code\b",
            r"\bauthentication\s+code\b",
            r"\brecovery\s+code\b",
        ],

        "urgency": [
            r"\burgent\b",
            r"\bimmediately\b",
            r"\bright\s+now\b",
            r"\bas\s+soon\s+as\s+possible\b",
            r"\bwithin\s+\d+\s+(?:minutes?|hours?)\b",
            r"\blast\s+warning\b",
            r"\byou\s+must\b",
            r"\byou\s+need\s+to\b",
            r"\baccount\s+will\s+be\s+(?:blocked|closed|suspended)\b",
        ],

        "threat_or_fear": [
            r"\b(?:arrest|arrested)\b",
            r"\bpolice\b",
            r"\blegal\s+action\b",
            r"\bcourt\b",
            r"\bfine\b",
            r"\bpenalty\b",
            r"\baccount\s+will\s+be\s+(?:blocked|closed|suspended)\b",
            r"\byou\s+will\s+lose\b",
            r"\bsecurity\s+breach\b",
        ],

        "authority_impersonation": [
            r"\bi(?:'m| am)\s+(?:from|calling from)\b",
            r"\bcalling\s+from\s+(?:the\s+)?bank\b",
            r"\bfrom\s+(?:the\s+)?bank\b",
            r"\bfrom\s+(?:the\s+)?police\b",
            r"\bfrom\s+(?:customer\s+)?support\b",
            r"\bfrom\s+(?:the\s+)?government\b",
            r"\bi(?:'m| am)\s+your\s+(?:boss|manager|supervisor)\b",
            r"\bi(?:'m| am)\s+your\s+(?:son|daughter|brother|sister|father|mother)\b",
        ],

        "secrecy_or_isolation": [
            r"\bdon't\s+tell\s+anyone\b",
            r"\bdo\s+not\s+tell\s+anyone\b",
            r"\bkeep\s+this\s+secret\b",
            r"\bkeep\s+this\s+between\s+us\b",
            r"\bdon't\s+discuss\s+this\b",
            r"\bdo\s+not\s+contact\s+anyone\b",
            r"\bdo\s+not\s+call\s+back\b",
        ],

        "callback_avoidance": [
            r"\bdo\s+not\s+call\s+back\b",
            r"\bdon't\s+call\s+back\b",
            r"\bno\s+need\s+to\s+call\s+back\b",
            r"\bavoid\s+calling\b",
            r"\bthis\s+number\s+cannot\s+receive\b",
            r"\bcall\s+back\s+later\b",
        ],

        "link_or_software": [
            r"\bclick\b",
            r"\bopen\s+(?:this|the)\s+(?:link|website|page)\b",
            r"\bdownload\b",
            r"\binstall\b",
            r"\bremote\s+desktop\b",
            r"\banydesk\b",
            r"\bteamviewer\b",
        ],

        "security_change": [
            r"\bdisable\b.{0,40}\bsecurity\b",
            r"\bturn\s+off\b.{0,40}\bsecurity\b",
            r"\bdisable\b.{0,40}\bantivirus\b",
            r"\bdisable\b.{0,40}\bfirewall\b",
            r"\bchange\b.{0,30}\bpassword\b",
            r"\breset\b.{0,30}\bpassword\b",
            r"\bdisable\b.{0,30}\b2fa\b",
        ],

        "personal_information": [
            r"\bdate\s+of\s+birth\b",
            r"\bdob\b",
            r"\bhome\s+address\b",
            r"\bphone\s+number\b",
            r"\baadhaar\b",
            r"\bpan\s+number\b",
            r"\bsocial\s+security\b",
            r"\bpersonal\s+information\b",
        ],
    }

    SIGNAL_STRENGTHS = {
        "financial": 0.75,
        "credential_request": 0.90,
        "otp_request": 0.95,
        "urgency": 0.65,
        "threat_or_fear": 0.70,
        "authority_impersonation": 0.60,
        "secrecy_or_isolation": 0.60,
        "callback_avoidance": 0.55,
        "link_or_software": 0.65,
        "security_change": 0.75,
        "personal_information": 0.55,
    }

    SIGNAL_LABELS = {
        "financial": "Financial transaction request detected.",
        "credential_request": "Sensitive credential request detected.",
        "otp_request": "OTP or verification-code request detected.",
        "urgency": "Urgency or pressure tactic detected.",
        "threat_or_fear": "Threat or fear-based pressure detected.",
        "authority_impersonation": "Possible authority/identity impersonation detected.",
        "secrecy_or_isolation": "Secrecy or isolation tactic detected.",
        "callback_avoidance": "Callback avoidance behavior detected.",
        "link_or_software": "Suspicious link or software action detected.",
        "security_change": "Security-setting change requested.",
        "personal_information": "Personal information request detected.",
    }

    def __init__(
        self,
        intent_analyzer: IntentAnalyzer | None = None,
    ) -> None:
        self.intent_analyzer = (
            intent_analyzer
            if intent_analyzer is not None
            else IntentAnalyzer()
        )

    def analyze(self, text: str) -> dict[str, Any]:
        """
        Analyze transcript context dynamically.

        The result remains backward-compatible with the existing
        VoiceShield firewall:

            score
            level
            action
            reasons
            matched_categories

        Additional fields provide richer evidence:

            intent
            signals
            evidence_strength
        """

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        normalized = " ".join(text.lower().split())

        if not normalized:
            return self._build_result(
                score=0.0,
                reasons=[],
                categories=[],
                signals=[],
                intent=self.intent_analyzer.analyze(""),
            )

        signals: list[dict[str, Any]] = []

        for category, patterns in self.SIGNAL_PATTERNS.items():

            matches = []

            for pattern in patterns:
                match = re.search(pattern, normalized)

                if match:
                    matches.append(match.group(0))

            if not matches:
                continue

            strength = self.SIGNAL_STRENGTHS.get(
                category,
                0.50,
            )

            signals.append(
                {
                    "type": category,
                    "strength": strength,
                    "matches": matches[:3],
                    "reason": self.SIGNAL_LABELS.get(
                        category,
                        "Suspicious conversation signal detected.",
                    ),
                }
            )

        intent_result = self.intent_analyzer.analyze(
            normalized
        )

        score = self._calculate_dynamic_score(
            signals=signals,
            intent=intent_result,
        )

        categories = [
            signal["type"]
            for signal in signals
        ]

        reasons = [
            signal["reason"]
            for signal in signals
        ]

        # Intent evidence is included as an explanation, but is not
        # counted twice when it already corresponds to a context signal.
        primary_intent = intent_result["primary_intent"]

        if primary_intent != "none":
            intent_label = self._intent_reason(
                primary_intent
            )

            if intent_label not in reasons:
                reasons.append(intent_label)

        if not reasons:
            reasons = [
                "No significant conversation risk detected."
            ]

        return self._build_result(
            score=score,
            reasons=reasons,
            categories=categories,
            signals=signals,
            intent=intent_result,
        )

    @classmethod
    def _calculate_dynamic_score(
        cls,
        signals: list[dict[str, Any]],
        intent: dict[str, Any],
    ) -> float:
        """
        Calculate risk from actual evidence.

        Formula:

            base = 1 - product(1 - signal_strength)

        This means additional independent evidence increases
        confidence without simply adding fixed category weights.

        Intent can provide a small corroboration bonus.
        """

        if not signals:
            base_score = 0.0
        else:
            probability_no_signal = 1.0

            for signal in signals:
                strength = float(
                    signal["strength"]
                )

                probability_no_signal *= (
                    1.0 - strength
                )

            base_score = (
                1.0 - probability_no_signal
            )

        intent_confidence = float(
            intent.get("confidence", 0.0)
        )

        if intent.get("primary_intent") != "none":
            corroboration_bonus = (
                0.10 * intent_confidence
            )
        else:
            corroboration_bonus = 0.0

        score = base_score + corroboration_bonus

        return round(
            min(max(score, 0.0), 1.0),
            4,
        )

    @staticmethod
    def _intent_reason(intent: str) -> str:

        reasons = {
            "credential_disclosure":
                "Caller appears to be requesting credential disclosure.",

            "otp_disclosure":
                "Caller appears to be requesting an OTP or verification code.",

            "financial_transfer":
                "Caller appears to be requesting a financial transaction.",

            "link_interaction":
                "Caller appears to be directing the user to interact with a link.",

            "software_installation":
                "Caller appears to be requesting software installation.",

            "security_change":
                "Caller appears to be requesting a security-setting change.",

            "personal_information":
                "Caller appears to be requesting personal information.",

            "callback_or_redirection":
                "Caller appears to be redirecting the user to another number.",

            "physical_action":
                "Caller appears to be requesting a physical action.",
        }

        return reasons.get(
            intent,
            "Caller intent could not be determined.",
        )

    @staticmethod
    def _build_result(
        score: float,
        reasons: list[str],
        categories: list[str],
        signals: list[dict[str, Any]],
        intent: dict[str, Any],
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

        return {
            "score": round(score, 4),
            "level": level,
            "action": action,
            "reasons": reasons,
            "matched_categories": categories,
            "signals": signals,
            "evidence_strength": round(score, 4),
            "intent": intent,
        }