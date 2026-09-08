import pytest

from challenge_response import (
    AdaptiveChallengeGenerator,
    ClaimExtractor,
    ResponseConsistencyEvaluator,
)


def test_location_claim_extraction():
    extractor = ClaimExtractor()

    claims = extractor.extract(
        "I'm at Delhi airport."
    )

    assert claims
    assert claims[0].claim_type == "location"
    assert "Delhi airport" in claims[0].subject


def test_adaptive_challenge_generation():
    generator = AdaptiveChallengeGenerator()

    challenge = generator.generate(
        "I'm at Delhi airport."
    )

    assert challenge is not None
    assert challenge.claim.claim_type == "location"
    assert challenge.question
    assert challenge.follow_up_question
    assert challenge.challenge_id


def test_no_claim_returns_none():
    generator = AdaptiveChallengeGenerator()

    challenge = generator.generate(
        "Hello, how are you?"
    )

    assert challenge is None


def test_consistent_response():
    generator = AdaptiveChallengeGenerator()

    challenge = generator.generate(
        "I'm at Delhi airport."
    )

    assert challenge is not None

    evaluator = ResponseConsistencyEvaluator()

    result = evaluator.evaluate(
        claim=challenge.claim,
        answer="I'm at terminal 3.",
        follow_up_answer="The IndiGo counter is nearby.",
    )

    assert result.confidence >= 0.65
    assert result.consistency_score > 0.0


def test_empty_response_fails():
    generator = AdaptiveChallengeGenerator()

    challenge = generator.generate(
        "I'm at Delhi airport."
    )

    assert challenge is not None

    evaluator = ResponseConsistencyEvaluator()

    result = evaluator.evaluate(
        claim=challenge.claim,
        answer="",
    )

    assert result.confidence == 0.0
    assert result.consistency_score == 0.0


def test_contradictory_response_is_penalized():
    generator = AdaptiveChallengeGenerator()

    challenge = generator.generate(
        "I'm at Delhi airport."
    )

    assert challenge is not None

    evaluator = ResponseConsistencyEvaluator()

    result = evaluator.evaluate(
        claim=challenge.claim,
        answer="No, I'm not there.",
    )

    assert result.contradiction_score == 1.0
    assert result.confidence < 0.80


def test_follow_up_response_is_supported():
    generator = AdaptiveChallengeGenerator()

    challenge = generator.generate(
        "I'm at Delhi airport."
    )

    assert challenge is not None

    evaluator = ResponseConsistencyEvaluator()

    first = evaluator.evaluate(
        claim=challenge.claim,
        answer="Terminal 3.",
    )

    second = evaluator.evaluate(
        claim=challenge.claim,
        answer="Terminal 3.",
        follow_up_answer="IndiGo counter is nearby.",
    )

    assert second.confidence >= first.confidence