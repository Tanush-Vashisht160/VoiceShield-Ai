from __future__ import annotations

import re
from typing import Any


class IntentAnalyzer:
    """
    Analyze what the caller is trying to make the other person do.

    This is intentionally separate from ContextAnalyzer.

    Intent answers:
        "What action is the caller attempting to obtain?"

    Examples:
        - disclose OTP
        - provide credentials
        - transfer money
        - click a link
        - install software
        - change security settings
        - call another number
        - share personal information

    The analyzer is rule-based and dependency-free so that the
    VoiceShield demo does not depend on an external API.
    """

    INTENT_PATTERNS = {
        "credential_disclosure": [
            r"\b(?:tell|give|share|provide|send)\b.{0,40}\bpassword\b",
            r"\b(?:tell|give|share|provide|send)\b.{0,40}\bpin\b",
            r"\b(?:tell|give|share|provide|send)\b.{0,40}\bpasscode\b",
            r"\b(?:tell|give|share|provide|send)\b.{0,40}\bcvv\b",
            r"\b(?:share|provide|send)\b.{0,40}\bcard\s+details\b",
            r"\b(?:share|provide|send)\b.{0,40}\blogin\s+details\b",
            r"\b(?:share|provide|send)\b.{0,40}\bcredentials\b",
        ],

        "otp_disclosure": [
            r"\b(?:tell|give|share|provide|send)\b.{0,40}\botp\b",
            r"\b(?:tell|give|share|provide|send)\b.{0,40}"
            r"(?:one[\s-]?time\s+password|verification\s+code)\b",
            r"\b(?:read|dictate)\b.{0,30}\botp\b",
            r"\b(?:read|dictate)\b.{0,30}\bverification\s+code\b",
        ],

        "financial_transfer": [
            r"\b(?:transfer|send|pay|deposit)\b.{0,50}\b(?:money|cash|funds)\b",
            r"\b(?:transfer|send)\b.{0,50}\b(?:upi|neft|imps)\b",
            r"\b(?:make|complete)\b.{0,30}\bpayment\b",
            r"\b(?:pay|send|transfer)\b.{0,30}\b(?:amount|funds)\b",
            r"\b(?:buy|purchase)\b.{0,40}\b(?:gift\s+card|voucher)\b",
            r"\b(?:send|transfer)\b.{0,40}\bcrypto(?:currency)?\b",
        ],

        "link_interaction": [
            r"\b(?:click|open|tap|visit)\b.{0,50}\b(?:link|url)\b",
            r"\bclick\s+(?:on\s+)?this\b",
            r"\bopen\s+(?:this|the)\s+(?:link|website|page)\b",
        ],

        "software_installation": [
            r"\b(?:install|download)\b.{0,50}"
            r"\b(?:app|application|software|program|remote\s+desktop)\b",
            r"\bdownload\b.{0,40}\b(?:anydesk|teamviewer|software)\b",
        ],

        "security_change": [
            r"\b(?:disable|turn\s+off|switch\s+off)\b.{0,50}"
            r"\b(?:security|antivirus|firewall|protection)\b",
            r"\b(?:change|reset)\b.{0,40}\bpassword\b",
            r"\b(?:change|reset)\b.{0,40}\bpin\b",
            r"\b(?:disable|remove)\b.{0,40}\b(?:2fa|two[\s-]?factor)\b",
        ],

        "personal_information": [
            r"\b(?:tell|give|share|provide|send)\b.{0,50}"
            r"\b(?:date\s+of\s+birth|dob|address|phone\s+number)\b",
            r"\b(?:tell|give|share|provide|send)\b.{0,50}"
            r"\b(?:aadhaar|pan\s+number|social\s+security)\b",
            r"\b(?:share|provide|send)\b.{0,40}\bpersonal\s+information\b",
        ],

        "callback_or_redirection": [
            r"\bcall\b.{0,50}\b(?:this|another|different)\s+number\b",
            r"\bcall\s+me\s+on\b",
            r"\bcontact\b.{0,30}\b(?:this|another)\s+number\b",
            r"\b(?:do\s+not|don't)\s+call\s+this\s+number\b",
        ],

        "physical_action": [
            r"\b(?:go|come)\b.{0,50}\b(?:office|branch|location|atm)\b",
            r"\b(?:visit|go\s+to)\b.{0,50}\b(?:bank|office|branch)\b",
        ],
    }

    INTENT_STRENGTHS = {
        "credential_disclosure": 0.95,
        "otp_disclosure": 0.98,
        "financial_transfer": 0.95,
        "link_interaction": 0.70,
        "software_installation": 0.85,
        "security_change": 0.85,
        "personal_information": 0.75,
        "callback_or_redirection": 0.65,
        "physical_action": 0.40,
    }

    INTENT_LABELS = {
        "credential_disclosure": "Credential disclosure",
        "otp_disclosure": "OTP disclosure",
        "financial_transfer": "Financial transfer",
        "link_interaction": "Link interaction",
        "software_installation": "Software installation",
        "security_change": "Security change",
        "personal_information": "Personal information disclosure",
        "callback_or_redirection": "Call redirection",
        "physical_action": "Physical action",
    }

    def analyze(self, text: str) -> dict[str, Any]:
        """
        Analyze caller intent from transcript text.

        Returns:
            Dictionary containing primary intent, secondary intents,
            confidence and detected intent evidence.
        """

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        normalized = " ".join(text.lower().split())

        if not normalized:
            return self._build_result(
                primary_intent="none",
                secondary_intents=[],
                confidence=0.0,
                evidence=[],
            )

        detected = []

        for intent, patterns in self.INTENT_PATTERNS.items():
            matches = []

            for pattern in patterns:
                match = re.search(pattern, normalized)

                if match:
                    matches.append(match.group(0))

            if not matches:
                continue

            strength = self.INTENT_STRENGTHS.get(intent, 0.50)

            detected.append(
                {
                    "intent": intent,
                    "label": self.INTENT_LABELS.get(
                        intent,
                        "Suspicious action",
                    ),
                    "strength": strength,
                    "matches": matches[:3],
                }
            )

        if not detected:
            return self._build_result(
                primary_intent="none",
                secondary_intents=[],
                confidence=0.0,
                evidence=[],
            )

        detected.sort(
            key=lambda item: item["strength"],
            reverse=True,
        )

        primary = detected[0]

        secondary = [
            item["intent"]
            for item in detected[1:]
        ]

        confidence = self._combine_confidence(
            [item["strength"] for item in detected]
        )

        return self._build_result(
            primary_intent=primary["intent"],
            secondary_intents=secondary,
            confidence=confidence,
            evidence=detected,
        )

    @staticmethod
    def _combine_confidence(strengths: list[float]) -> float:
        """
        Combine independent intent evidence.

        More evidence increases confidence, but the result is
        always bounded between 0 and 1.
        """

        if not strengths:
            return 0.0

        probability_not_supported = 1.0

        for strength in strengths:
            probability_not_supported *= 1.0 - strength

        confidence = 1.0 - probability_not_supported

        return round(
            min(max(confidence, 0.0), 1.0),
            4,
        )

    @staticmethod
    def _build_result(
        primary_intent: str,
        secondary_intents: list[str],
        confidence: float,
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:

        return {
            "primary_intent": primary_intent,
            "secondary_intents": secondary_intents,
            "confidence": round(confidence, 4),
            "evidence": evidence,
        }