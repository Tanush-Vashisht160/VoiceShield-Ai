from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .adaptive_challenge import (
    AdaptiveChallengeGenerator,
    ResponseConsistencyEvaluator,
)
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

        self.adaptive_challenge_generator = AdaptiveChallengeGenerator()
        self.response_consistency_evaluator = ResponseConsistencyEvaluator()

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
    def start_adaptive_challenge(
        self,
        transcript: str,
    ) -> dict[str, Any] | None:
        """
        Generate a challenge from a claim detected in the
        current conversation.

        Returns None when no suitable claim is detected.
        """

        adaptive_challenge = (
            self.adaptive_challenge_generator.generate(
                transcript
            )
        )

        if adaptive_challenge is None:
            return None

        challenge = self.challenge_generator.generate()

        session = ChallengeSession(
            challenge_id=challenge["challenge_id"],
            phrase=challenge["phrase"],
            created_at=challenge["created_at"],
            expires_at=challenge["expires_at"],
            max_attempts=3,
        )

        session.adaptive_challenge = (
            adaptive_challenge.to_dict()
        )

        session.mark_waiting_for_response()

        self.sessions[
            challenge["challenge_id"]
        ] = session

        return {
            "challenge_id": challenge["challenge_id"],
            "claim": adaptive_challenge.claim.to_dict(),
            "question": adaptive_challenge.question,
            "follow_up_question": (
                adaptive_challenge.follow_up_question
            ),
            "challenge_type": (
                adaptive_challenge.challenge_type
            ),
            "expires_at": challenge["expires_at"],
            "max_attempts": 3,
        }
        def verify_adaptive_response(
            self,
            challenge_id: str,
            answer: str,
            follow_up_answer: str | None = None,
            response_delay_seconds: float | None = None,
        ) -> dict[str, Any]:
            """
            Evaluate an answer to an adaptive challenge.
            """

            session = self.get_session(challenge_id)

            if session is None:
                raise KeyError(
                    f"Challenge session not found: {challenge_id}"
                )

            if session.is_expired():
                session.mark_expired()

                return {
                    "challenge_id": challenge_id,
                    "passed": False,
                    "confidence": 0.0,
                    "status": "REJECTED",
                    "reason": "Adaptive challenge expired.",
                }

            adaptive_data = session.adaptive_challenge

            if not adaptive_data:
                raise ValueError(
                    "This session does not contain an adaptive challenge."
                )

            claim_data = adaptive_data["claim"]

            from .adaptive_challenge import Claim

            claim = Claim(
                text=claim_data["text"],
                claim_type=claim_data["claim_type"],
                subject=claim_data["subject"],
                confidence=float(
                    claim_data.get("confidence", 0.0)
                ),
            )

            result = self.response_consistency_evaluator.evaluate(
                claim=claim,
                answer=answer,
                follow_up_answer=follow_up_answer,
            )

            session.adaptive_answer = answer
            session.adaptive_follow_up_answer = (
                follow_up_answer
            )
            session.adaptive_consistency_result = (
                result.to_dict()
            )

            # Optional timing signal.
            timing_score = 1.0

            if response_delay_seconds is not None:
                if response_delay_seconds <= 3:
                    timing_score = 1.0
                elif response_delay_seconds <= 8:
                    timing_score = 0.8
                elif response_delay_seconds <= 15:
                    timing_score = 0.6
                else:
                    timing_score = 0.4

            final_confidence = (
                result.confidence * 0.85
                + timing_score * 0.15
            )

            final_confidence = max(
                0.0,
                min(1.0, final_confidence),
            )

            passed = final_confidence >= 0.65

            if passed:
                status = "CONSISTENT"
            elif final_confidence >= 0.40:
                status = "INCONCLUSIVE"
            else:
                status = "INCONSISTENT"

            return {
                "challenge_id": challenge_id,
                "passed": passed,
                "confidence": round(
                    final_confidence,
                    4,
                ),
                "status": status,
                "timing_score": round(
                    timing_score,
                    4,
                ),
                "consistency": result.to_dict(),
            }
    
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
