from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .challenge_generator import ChallengeGenerator
from .challenge_session import ChallengeSession
from .models import ChallengeAuthenticationResult
from .phrase_verifier import ChallengePhraseVerifier

if TYPE_CHECKING:
    from app.detector import DeepfakeDetector
    from app.risk_engine import RiskEngine
    from app.speaker_verifier import SpeakerVerifier


class ChallengeService:
    """Coordinate challenge generation, verification and final authentication decisions."""

    def __init__(
        self,
        challenge_generator: ChallengeGenerator | None = None,
        phrase_verifier: ChallengePhraseVerifier | None = None,
        risk_engine: Any | None = None,
        speaker_verifier: Any | None = None,
        detector: Any | None = None,
    ) -> None:
        self.challenge_generator = challenge_generator or ChallengeGenerator()
        self.phrase_verifier = phrase_verifier or ChallengePhraseVerifier()
        self.risk_engine = risk_engine
        self.speaker_verifier = speaker_verifier
        self.detector = detector
        self.sessions: dict[str, ChallengeSession] = {}

    def start_challenge(self, phrase: str | None = None) -> dict[str, Any]:
        challenge = self.challenge_generator.generate()
        if phrase is not None:
            challenge["phrase"] = phrase
            challenge["number"] = None
            challenge["color"] = None
            challenge["word"] = None

        session = ChallengeSession(
            challenge_id=challenge["challenge_id"],
            phrase=challenge["phrase"],
            created_at=challenge["created_at"],
            expires_at=challenge["expires_at"],
            max_attempts=3,
        )
        session.mark_waiting_for_response()
        self.sessions[challenge["challenge_id"]] = session
        return challenge

    def get_session(self, challenge_id: str) -> ChallengeSession | None:
        return self.sessions.get(challenge_id)

    def verify_response(
        self,
        challenge_id: str,
        transcript: str | None = None,
        voice_prediction: str | None = None,
        voice_fake_score: float | None = None,
        speaker_verified: bool | None = None,
        speaker_confidence: float | None = None,
        verification_error: str | None = None,
    ) -> ChallengeAuthenticationResult:
        session = self.get_session(challenge_id)
        if session is None:
            raise KeyError(f"Challenge session not found: {challenge_id}")

        if session.is_expired():
            session.mark_expired()
            return ChallengeAuthenticationResult(
                challenge_id=challenge_id,
                challenge_passed=False,
                challenge_confidence=0.0,
                speaker_verified=speaker_verified,
                speaker_confidence=speaker_confidence,
                voice_authentic=False if voice_prediction else None,
                voice_confidence=None,
                final_status="REJECTED",
                risk_score=100.0,
                recommendation="Challenge expired. Do not proceed with the call.",
                reasons=["Challenge expired before verification was completed."],
                completed_at=datetime.now(timezone.utc),
            )

        session.response_transcript = transcript or ""
        session.mark_processing()

        phrase_result = self.phrase_verifier.verify(session.phrase, transcript or "")
        challenge_passed = bool(phrase_result.get("passed"))
        challenge_confidence = float(phrase_result.get("confidence", 0.0))

        voice_authentic = None
        voice_confidence = None
        if voice_prediction is not None:
            voice_authentic = str(voice_prediction).lower() == "real"
            voice_confidence = 1.0 - float(voice_fake_score or 0.0) if voice_fake_score is not None else 0.0

        if verification_error:
            final_status = "INCONCLUSIVE"
            recommendation = "Exercise caution and use an alternate verification method."
            reasons = [verification_error]
            risk_score = 60.0
        elif challenge_passed is False:
            final_status = "REJECTED"
            recommendation = "Do not proceed with the call."
            reasons = ["The spoken challenge did not match the generated phrase."]
            risk_score = 90.0
        elif speaker_verified is False:
            final_status = "SUSPICIOUS"
            recommendation = "Additional verification is required before continuing."
            reasons = ["Speaker verification did not match the expected voice."]
            risk_score = 75.0
        elif voice_authentic is False:
            final_status = "REJECTED"
            recommendation = "Do not proceed with the call."
            reasons = ["The response audio appears synthetic or manipulated."]
            risk_score = 95.0
        elif (
            challenge_passed is True
            and speaker_verified is True
            and voice_authentic is True
        ):
            final_status = "AUTHENTICATED"
            recommendation = "Safe to proceed"
            reasons = ["Challenge, speaker, and voice authenticity checks were consistent."]
            risk_score = 8.0
        else:
            final_status = "INCONCLUSIVE"
            recommendation = "Exercise caution and use an alternate verification method."
            reasons = ["One or more verification layers could not be completed with confidence."]
            risk_score = 55.0

        if session.attempt_count < session.max_attempts:
            session.record_attempt()

        session.challenge_verification_result = {
            "passed": challenge_passed,
            "confidence": challenge_confidence,
            "final_status": final_status,
        }

        if final_status == "AUTHENTICATED":
            session.mark_verified()
        elif final_status in {"REJECTED", "SUSPICIOUS"}:
            session.mark_failed()
        else:
            session.mark_processing()

        result = ChallengeAuthenticationResult(
            challenge_id=challenge_id,
            challenge_passed=challenge_passed,
            challenge_confidence=challenge_confidence,
            speaker_verified=speaker_verified,
            speaker_confidence=speaker_confidence,
            voice_authentic=voice_authentic,
            voice_confidence=voice_confidence,
            final_status=final_status,
            risk_score=risk_score,
            recommendation=recommendation,
            reasons=reasons,
            completed_at=datetime.now(timezone.utc),
        )
        return result
