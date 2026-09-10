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
    Combine available security signals into a dynamic 0-100 risk score.

    Signals:
        fake_score:
            Probability that the audio is AI-generated.
            Range: 0.0 - 1.0

        speaker_mismatch_score:
            Severity of speaker identity mismatch.
            Range: 0.0 - 1.0

        context_risk_score:
            Risk from conversation/context analysis.
            Range: 0.0 - 1.0

    The original importance of the signals remains:
        fake       = 50%
        speaker    = 30%
        context    = 20%

    However, these weights are normalized over the evidence that is
    actually available for the current analysis.

    This prevents missing evidence from being interpreted as
    zero-risk evidence.
    """

    def __init__(
        self,
        fake_weight: float = 0.50,
        speaker_weight: float = 0.30,
        context_weight: float = 0.20,
    ):
        weights = {
            "fake": fake_weight,
            "speaker": speaker_weight,
            "context": context_weight,
        }

        for name, weight in weights.items():
            if not isinstance(weight, (int, float)):
                raise TypeError(
                    f"{name}_weight must be a number."
                )

            if weight < 0:
                raise ValueError(
                    f"{name}_weight cannot be negative."
                )

        total = sum(weights.values())

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

    @staticmethod
    def _validate_availability(
        value: float,
        name: str,
    ) -> float:
        """
        Validate evidence availability/strength.

        0.0 means unavailable.
        1.0 means fully available.
        Values between 0 and 1 represent partial evidence strength.
        """

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
        fake_availability: float = 1.0,
        speaker_availability: float = 0.0,
        context_availability: float = 0.0,
    ) -> RiskAssessment:
        """
        Calculate dynamic security risk.

        Availability values describe whether the corresponding
        evidence was actually available for this analysis.

        Example:

            Audio only:
                fake_availability = 1.0
                speaker_availability = 0.0
                context_availability = 0.0

            Audio + speaker reference:
                fake_availability = 1.0
                speaker_availability = 1.0
                context_availability = 0.0

            Full analysis:
                fake_availability = 1.0
                speaker_availability = 1.0
                context_availability = 1.0
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

        fake_availability = self._validate_availability(
            fake_availability,
            "fake_availability",
        )

        speaker_availability = self._validate_availability(
            speaker_availability,
            "speaker_availability",
        )

        context_availability = self._validate_availability(
            context_availability,
            "context_availability",
        )

        # ---------------------------------------------------------
        # 1. Calculate effective weights for the evidence available
        # ---------------------------------------------------------

        effective_fake_weight = (
            self.fake_weight * fake_availability
        )

        effective_speaker_weight = (
            self.speaker_weight * speaker_availability
        )

        effective_context_weight = (
            self.context_weight * context_availability
        )

        total_effective_weight = (
            effective_fake_weight
            + effective_speaker_weight
            + effective_context_weight
        )

        # Fake detection is the primary analysis signal, so this
        # should normally always be available.
        if total_effective_weight <= 0:
            raise ValueError(
                "At least one security signal must be available."
            )

        # ---------------------------------------------------------
        # 2. Normalize the weights dynamically
        # ---------------------------------------------------------

        normalized_fake_weight = (
            effective_fake_weight
            / total_effective_weight
        )

        normalized_speaker_weight = (
            effective_speaker_weight
            / total_effective_weight
        )

        normalized_context_weight = (
            effective_context_weight
            / total_effective_weight
        )

        # ---------------------------------------------------------
        # 3. Calculate base risk
        # ---------------------------------------------------------

        base_risk = (
            fake_score * normalized_fake_weight
            + speaker_mismatch_score * normalized_speaker_weight
            + context_risk_score * normalized_context_weight
        )

        # ---------------------------------------------------------
        # 4. Calculate corroboration between available signals
        # ---------------------------------------------------------

        interaction_values = []

        if (
            fake_availability > 0
            and speaker_availability > 0
        ):
            interaction_values.append(
                fake_score * speaker_mismatch_score
            )

        if (
            fake_availability > 0
            and context_availability > 0
        ):
            interaction_values.append(
                fake_score * context_risk_score
            )

        if (
            speaker_availability > 0
            and context_availability > 0
        ):
            interaction_values.append(
                speaker_mismatch_score
                * context_risk_score
            )

        if interaction_values:
            corroboration = (
                sum(interaction_values)
                / len(interaction_values)
            )
        else:
            corroboration = 0.0

        # Corroboration is deliberately limited so that the
        # interaction term cannot dominate the primary evidence.
        corroboration_bonus = 0.10 * corroboration

        # ---------------------------------------------------------
        # 5. Final risk
        # ---------------------------------------------------------

        final_risk = base_risk + corroboration_bonus

        final_risk = max(
            0.0,
            min(1.0, final_risk),
        )

        score = final_risk * 100.0

        reasons = []

        # ---------------------------------------------------------
        # 6. Explain the individual signals
        # ---------------------------------------------------------

        if fake_availability > 0:

            if fake_score >= 0.70:
                reasons.append(
                    "High probability of synthetic/deepfake audio."
                )

            elif fake_score >= 0.40:
                reasons.append(
                    "Moderate probability of synthetic/deepfake audio."
                )

        if speaker_availability > 0:

            if speaker_mismatch_score >= 0.70:
                reasons.append(
                    "High speaker identity mismatch detected."
                )

            elif speaker_mismatch_score >= 0.40:
                reasons.append(
                    "Possible speaker identity mismatch detected."
                )

        if context_availability > 0:

            if context_risk_score >= 0.70:
                reasons.append(
                    "High-risk conversation context detected."
                )

            elif context_risk_score >= 0.40:
                reasons.append(
                    "Moderate-risk conversation context detected."
                )

        # ---------------------------------------------------------
        # 7. Explain corroborating evidence
        # ---------------------------------------------------------

        available_signal_count = sum(
            [
                fake_availability > 0,
                speaker_availability > 0,
                context_availability > 0,
            ]
        )

        if (
            available_signal_count >= 2
            and corroboration >= 0.50
        ):
            reasons.append(
                "Multiple independent security signals "
                "corroborate the elevated risk."
            )

        # ---------------------------------------------------------
        # 8. Final risk level and action
        # ---------------------------------------------------------

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