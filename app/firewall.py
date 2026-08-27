from pathlib import Path
from typing import Any

from app.context_analyzer import ContextAnalyzer
from app.detector import DeepfakeDetector
from app.realtime_engine import RealtimeDetectionEngine
from app.risk_engine import RiskEngine
from app.speaker_verifier import SpeakerVerifier
from app.security_decision import SecurityDecisionEngine

class VoiceSecurityFirewall:
    """
    Main orchestration layer for VoiceShield AI.

    Combines:
    1. Real-time audio chunking / streaming analysis
    2. Deepfake voice detection
    3. Speaker verification against reference audio
    4. Conversation & contextual NLP risk analysis (via ContextAnalyzer)
    5. Dynamic risk scoring
    6. Automated security actions (ALLOW / WARN / BLOCK)
    """

    def __init__(self) -> None:
        print("Initializing Voice Security Firewall...")

        self.detector = DeepfakeDetector()
        self.realtime_engine = RealtimeDetectionEngine(
            detector=self.detector
        )
        self.speaker_verifier = SpeakerVerifier()
        self.risk_engine = RiskEngine()
        self.context_analyzer = ContextAnalyzer()
        self.decision_engine = SecurityDecisionEngine()
        print()
        print("Voice Security Firewall initialized successfully.")

    @staticmethod
    def _validate_score(
        value: Any,
        name: str,
    ) -> float:
        """
        Validate and convert a score to a float within [0.0, 1.0].
        """
        try:
            score = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Validation Error: '{name}' must be a numeric value. "
                f"Received type: {type(value).__name__}"
            ) from exc

        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"Validation Error: '{name}' must be bounded between 0.0 and 1.0. "
                f"Received value: {score}"
            )

        return score

    def analyze_call(
        self,
        audio_path: str | Path,
        reference_audio: str | Path | None = None,
        speaker_mismatch_score: float | None = None,
        context_risk_score: float | None = None,
        transcript: str | None = None,
        realtime: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze an audio file for deepfake traits, speaker mismatch,
        transcript risk, and overall risk.

        Args:
            audio_path:
                Path to the target audio file.

            reference_audio:
                Path to a trusted speaker reference sample.

            speaker_mismatch_score:
                Optional pre-calculated mismatch score in [0, 1].

            context_risk_score:
                Optional explicit context risk score in [0, 1].

            transcript:
                Optional conversation transcript.

            realtime:
                If True, use RealtimeDetectionEngine.
                Otherwise, use DeepfakeDetector.

        Returns:
            Complete firewall assessment.
        """

        path = Path(audio_path)

        # ------------------------------------------------------------
        # 1. INPUT AUDIO VALIDATION
        # ------------------------------------------------------------

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found at specified path: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Provided audio path is a directory, not a valid file: {path}"
            )

        # ------------------------------------------------------------
        # 2. REFERENCE AUDIO VALIDATION
        #
        # Validate this BEFORE running the audio detector.
        # This guarantees a missing reference file raises the expected
        # FileNotFoundError even when the target audio is invalid.
        # ------------------------------------------------------------

        reference_path = None

        if reference_audio is not None:

            reference_path = Path(reference_audio)

            if not reference_path.exists():
                raise FileNotFoundError(
                    f"Reference audio file not found: {reference_path}"
                )

            if not reference_path.is_file():
                raise ValueError(
                    f"Provided reference path is not a file: {reference_path}"
                )

        # ------------------------------------------------------------
        # 3. CONTEXT RISK EVALUATION
        # ------------------------------------------------------------

        context_result: dict[str, Any] | None = None

        if transcript is not None:

            context_result = self.context_analyzer.analyze(
                transcript
            )

            # Explicit context_risk_score takes priority.
            if context_risk_score is None:
                context_risk_score = float(
                    context_result["score"]
                )

        if context_risk_score is None:
            context_risk_score = 0.0

        context_risk_score = self._validate_score(
            context_risk_score,
            "context_risk_score",
        )

        # ------------------------------------------------------------
        # 4. SPEAKER MISMATCH SCORE VALIDATION
        # ------------------------------------------------------------

        if speaker_mismatch_score is not None:

            speaker_mismatch_score = self._validate_score(
                speaker_mismatch_score,
                "speaker_mismatch_score",
            )

        # ------------------------------------------------------------
        # 5. VOICE AUTHENTICITY / DEEPFAKE DETECTION
        # ------------------------------------------------------------

        if realtime:

            detection = self.realtime_engine.analyze(path)

            fake_score = float(
                detection["average_fake_score"]
            )

            voice_detection = {
                **detection,
                "prediction": detection["prediction"],
                "fake_score": fake_score,
                "real_score": float(
                    detection["average_real_score"]
                ),
                "confidence": float(
                    detection["confidence"]
                ),
            }

        else:

            detection = self.detector.predict(path)

            fake_score = float(
                detection["fake_score"]
            )

            voice_detection = detection

        # ------------------------------------------------------------
        # 6. SPEAKER VERIFICATION
        # ------------------------------------------------------------

        speaker_result = None

        if reference_path is not None:

            speaker_result = self.speaker_verifier.verify(
                reference_path,
                path,
            )

            # If the caller did not provide a mismatch score,
            # calculate it from speaker similarity.
            if speaker_mismatch_score is None:

                similarity = float(
                    speaker_result["score"]
                )

                speaker_mismatch_score = max(
                    0.0,
                    min(
                        1.0,
                        1.0 - similarity,
                    ),
                )

        if speaker_mismatch_score is None:
            speaker_mismatch_score = 0.0

        speaker_mismatch_score = self._validate_score(
            speaker_mismatch_score,
            "speaker_mismatch_score",
        )

        # ------------------------------------------------------------
        # 7. RISK ENGINE CALCULATION
        # ------------------------------------------------------------

        risk = self.risk_engine.calculate(
            fake_score=fake_score,
            speaker_mismatch_score=speaker_mismatch_score,
            context_risk_score=context_risk_score,
        )
        decision = self.decision_engine.decide(
            risk_score=risk.score,
            risk_level=risk.level,
            risk_reasons=risk.reasons,
            fake_score=fake_score,
            speaker_mismatch_score=speaker_mismatch_score,
            context_risk_score=context_risk_score,
        )
        # ------------------------------------------------------------
        # 8. FINAL RESULT
        # ------------------------------------------------------------

        return {
            "audio_file": str(path),

            "voice_detection": voice_detection,

            "speaker_verification": speaker_result,

            "context_analysis": context_result,

            "risk_inputs": {
                "fake_score": fake_score,
                "speaker_mismatch_score": speaker_mismatch_score,
                "context_risk_score": context_risk_score,
            },

            "risk": {
                "score": risk.score,
                "level": risk.level,
                "action": risk.action,
                "reasons": risk.reasons,
            },

            "decision": {
    "action": decision.action,
    "risk_score": decision.risk_score,
    "level": decision.level,
    "explanation": decision.explanation,
    "alerts": decision.alerts,
    "recommended_actions": decision.recommended_actions,
},
        }