from dataclasses import dataclass


@dataclass
class RiskAssessment:
    """Final security assessment produced by the risk engine."""

    score: float
    level: str
    action: str
    reasons: list[str]


class RiskEngine:
    """
    Combine security signals into a single 0-100 risk score.

    Signals:
        fake_score:
            Probability that the audio is AI-generated.
            Range: 0.0 - 1.0

        speaker_mismatch_score:
            Probability/severity of speaker identity mismatch.
            Range: 0.0 - 1.0

        context_risk_score:
            Risk from conversation/context analysis.
            Range: 0.0 - 1.0
    """

    def __init__(
        self,
        fake_weight: float = 0.50,
        speaker_weight: float = 0.30,
        context_weight: float = 0.20,
    ):
        total = fake_weight + speaker_weight + context_weight

        if total <= 0:
            raise ValueError(
                "Risk weights must have a positive total."
            )

        self.fake_weight = fake_weight / total
        self.speaker_weight = speaker_weight / total
        self.context_weight = context_weight / total

    @staticmethod
    def _validate_score(value: float, name: str) -> float:
        """Validate a score that must be between 0 and 1."""

        if not isinstance(value, (int, float)):
            raise TypeError(
                f"{name} must be a number."
            )

        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{name} must be between 0 and 1."
            )

        return float(value)

    def calculate(
        self,
        fake_score: float,
        speaker_mismatch_score: float = 0.0,
        context_risk_score: float = 0.0,
    ) -> RiskAssessment:
        """
        Calculate the final call security risk.

        Returns:
            RiskAssessment with:
                - score: 0-100
                - level: LOW/MEDIUM/HIGH
                - action: ALLOW/WARN/BLOCK
                - reasons: explanation of the risk
        """

        fake_score = self._validate_score(
            fake_score,
            "fake_score",
        )

        speaker_mismatch_score = self._validate_score(
            speaker_mismatch_score,
            "speaker_mismatch_score",
        )

        context_risk_score = self._validate_score(
            context_risk_score,
            "context_risk_score",
        )

        # Weighted risk calculation.
        score = (
            fake_score * self.fake_weight
            + speaker_mismatch_score * self.speaker_weight
            + context_risk_score * self.context_weight
        ) * 100.0

        # Safety clamp.
        score = max(0.0, min(100.0, score))

        reasons = []

        # Deepfake signal.
        if fake_score >= 0.70:
            reasons.append(
                "High probability of synthetic/deepfake audio."
            )
        elif fake_score >= 0.40:
            reasons.append(
                "Moderate probability of synthetic/deepfake audio."
            )

        # Speaker signal.
        if speaker_mismatch_score >= 0.70:
            reasons.append(
                "High speaker identity mismatch detected."
            )
        elif speaker_mismatch_score >= 0.40:
            reasons.append(
                "Possible speaker identity mismatch detected."
            )

        # Context signal.
        if context_risk_score >= 0.70:
            reasons.append(
                "High-risk conversation context detected."
            )
        elif context_risk_score >= 0.40:
            reasons.append(
                "Moderate-risk conversation context detected."
            )

        # Final risk level and action.
        if score >= 70:
            level = "HIGH"
            action = "BLOCK"
        elif score >= 40:
            level = "MEDIUM"
            action = "WARN"
        else:
            level = "LOW"
            action = "ALLOW"

        if not reasons:
            reasons.append(
                "No significant security risk detected."
            )

        return RiskAssessment(
            score=round(score, 2),
            level=level,
            action=action,
            reasons=reasons,
        )