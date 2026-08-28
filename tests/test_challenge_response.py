from datetime import datetime, timedelta, timezone

import pytest

from challenge_response import (
    ChallengeGenerator,
    ChallengePhraseVerifier,
    ChallengeService,
    ChallengeSession,
    ChallengeSessionState,
)


@pytest.fixture
def challenge_service():
    return ChallengeService()


def test_challenge_generation():
    generator = ChallengeGenerator()
    challenge = generator.generate()

    assert challenge["challenge_id"]
    assert challenge["phrase"]
    assert len(challenge["phrase"].split()) >= 3
    assert challenge["created_at"] <= challenge["expires_at"]
    assert " " in challenge["phrase"]


def test_challenge_uniqueness_across_generations():
    generator = ChallengeGenerator()
    challenge_ids = {generator.generate()["challenge_id"] for _ in range(25)}

    assert len(challenge_ids) == 25


def test_challenge_expiration():
    generator = ChallengeGenerator()
    challenge = generator.generate()

    assert challenge["expires_at"] > challenge["created_at"]


def test_session_state_transitions():
    session = ChallengeSession(
        challenge_id="challenge-1",
        phrase="47 blue mango",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
        max_attempts=3,
    )

    assert session.state == ChallengeSessionState.CREATED

    session.mark_waiting_for_response()
    assert session.state == ChallengeSessionState.WAITING_FOR_RESPONSE

    session.record_attempt()
    session.mark_processing()
    assert session.state == ChallengeSessionState.PROCESSING

    session.mark_verified()
    assert session.state == ChallengeSessionState.VERIFIED


def test_exact_phrase_match():
    verifier = ChallengePhraseVerifier()
    result = verifier.verify("47 blue mango", "47 blue mango")

    assert result["passed"] is True
    assert result["normalized_expected"] == "47 blue mango"
    assert result["normalized_actual"] == "47 blue mango"


def test_normalized_phrase_match():
    verifier = ChallengePhraseVerifier()
    result = verifier.verify("47 blue mango", "forty seven blue mango")

    assert result["passed"] is True
    assert result["confidence"] >= 0.85


def test_incorrect_phrase_rejected():
    verifier = ChallengePhraseVerifier()
    result = verifier.verify("47 blue mango", "47 blue orange")

    assert result["passed"] is False


def test_empty_transcript_rejected():
    verifier = ChallengePhraseVerifier()
    result = verifier.verify("47 blue mango", "")

    assert result["passed"] is False
    assert result["normalized_actual"] == ""


def test_excessive_attempts_blocked():
    session = ChallengeSession(
        challenge_id="challenge-2",
        phrase="82 green tiger",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
        max_attempts=2,
    )

    assert session.can_attempt() is True
    session.record_attempt()
    assert session.can_attempt() is True
    session.record_attempt()
    assert session.can_attempt() is False
    assert session.state == ChallengeSessionState.FAILED


def test_expired_challenge_rejected():
    session = ChallengeSession(
        challenge_id="challenge-3",
        phrase="16 yellow river",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        max_attempts=3,
    )

    assert session.is_expired() is True
    assert session.can_attempt() is False


def test_successful_authentication_result_logic(challenge_service):
    challenge = challenge_service.start_challenge(phrase="47 blue mango")
    result = challenge_service.verify_response(
        challenge_id=challenge["challenge_id"],
        transcript="47 blue mango",
        voice_prediction="real",
        voice_fake_score=0.08,
        speaker_verified=True,
        speaker_confidence=0.96,
    )

    assert result.final_status == "AUTHENTICATED"
    assert result.challenge_passed is True
    assert result.voice_authentic is True
    assert result.speaker_verified is True


def test_external_verification_failure_makes_result_inconclusive(challenge_service):
    challenge = challenge_service.start_challenge(phrase="47 blue mango")

    result = challenge_service.verify_response(
        challenge_id=challenge["challenge_id"],
        transcript="47 blue mango",
        voice_prediction=None,
        voice_fake_score=None,
        speaker_verified=None,
        speaker_confidence=None,
        verification_error="speaker service unavailable",
    )

    assert result.final_status == "INCONCLUSIVE"
    assert result.recommendation.startswith("Exercise caution")


def test_suspicious_mismatch_is_flagged(challenge_service):
    challenge = challenge_service.start_challenge(phrase="47 blue mango")
    result = challenge_service.verify_response(
        challenge_id=challenge["challenge_id"],
        transcript="47 blue mango",
        voice_prediction="real",
        voice_fake_score=0.10,
        speaker_verified=False,
        speaker_confidence=0.20,
    )

    assert result.final_status == "SUSPICIOUS"
