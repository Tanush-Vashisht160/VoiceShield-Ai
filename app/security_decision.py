from dataclasses import dataclass
from typing import Any


@dataclass
class SecurityDecision:
    """
    Final action recommended by Voice Security Firewall.
    """

    action: str
    risk_score: float
    level: str
    explanation: str
    alerts: list[str]
    recommended_actions: list[str]


class SecurityDecisionEngine:
    """
    Converts the risk assessment into an explainable
    security response.

    Possible actions:

        ALLOW
        WARN
        HOLD
        BLOCK
    """

    def decide(
        self,
        risk_score: float,
        risk_level: str,
        risk_reasons: list[str],
        fake_score: float,
        speaker_mismatch_score: float,
        context_risk_score: float,
    ) -> SecurityDecision:

        # ---------------------------------------------------------
        # Validate inputs
        # ---------------------------------------------------------

        if not 0.0 <= risk_score <= 100.0:
            raise ValueError(
                "risk_score must be between 0 and 100."
            )

        if not 0.0 <= fake_score <= 1.0:
            raise ValueError(
                "fake_score must be between 0 and 1."
            )

        if not 0.0 <= speaker_mismatch_score <= 1.0:
            raise ValueError(
                "speaker_mismatch_score must be between 0 and 1."
            )

        if not 0.0 <= context_risk_score <= 1.0:
            raise ValueError(
                "context_risk_score must be between 0 and 1."
            )

        alerts = []
        recommended_actions = []

        # ---------------------------------------------------------
        # Detect individual threats
        # ---------------------------------------------------------

        if fake_score >= 0.70:
            alerts.append(
                "AI-generated or manipulated voice suspected."
            )

        if speaker_mismatch_score >= 0.70:
            alerts.append(
                "Caller identity does not match the reference speaker."
            )

        if context_risk_score >= 0.70:
            alerts.append(
                "Suspicious conversation behavior detected."
            )

        # ---------------------------------------------------------
        # Critical combination:
        #
        # Fake voice + identity mismatch
        # ---------------------------------------------------------

        if (
            fake_score >= 0.70
            and speaker_mismatch_score >= 0.70
        ):
            action = "BLOCK"

            explanation = (
                "Multiple independent security signals indicate "
                "a likely voice impersonation attack."
            )

            recommended_actions.extend(
                [
                    "Block or terminate the call.",
                    "Do not disclose OTPs, passwords, or financial information.",
                    "Request independent identity verification.",
                    "Log the incident for security review.",
                ]
            )

        # ---------------------------------------------------------
        # High context risk
        # ---------------------------------------------------------

        elif (
            fake_score >= 0.70
            or speaker_mismatch_score >= 0.70
        ) and context_risk_score >= 0.70:

            action = "HOLD"

            explanation = (
                "The call contains a strong voice-security signal "
                "combined with suspicious conversation behavior."
            )

            recommended_actions.extend(
                [
                    "Place the call on temporary hold.",
                    "Request callback verification.",
                    "Do not share sensitive information.",
                ]
            )

        # ---------------------------------------------------------
        # Medium risk
        # ---------------------------------------------------------

        elif risk_score >= 40:

            action = "WARN"

            explanation = (
                "The call contains one or more security signals "
                "that require additional verification."
            )

            recommended_actions.extend(
                [
                    "Warn the user.",
                    "Request additional verification.",
                    "Avoid sharing sensitive information.",
                ]
            )

        # ---------------------------------------------------------
        # Low risk
        # ---------------------------------------------------------

        else:

            action = "ALLOW"

            explanation = (
                "No significant voice-security threat was detected."
            )

            recommended_actions.append(
                "Continue the call normally."
            )

        # ---------------------------------------------------------
        # Fallback alert
        # ---------------------------------------------------------

        if not alerts:
            alerts.append(
                "No critical security indicators detected."
            )

        return SecurityDecision(
            action=action,
            risk_score=round(risk_score, 2),
            level=risk_level,
            explanation=explanation,
            alerts=alerts,
            recommended_actions=recommended_actions,
        )