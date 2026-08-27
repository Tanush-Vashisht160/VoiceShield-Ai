import pytest

from app.security_decision import SecurityDecisionEngine


def test_safe_call():

    engine = SecurityDecisionEngine()

    result = engine.decide(
        risk_score=10,
        risk_level="LOW",
        risk_reasons=[],
        fake_score=0.05,
        speaker_mismatch_score=0.05,
        context_risk_score=0.05,
    )

    assert result.action == "ALLOW"


def test_fake_voice_blocks():

    engine = SecurityDecisionEngine()

    result = engine.decide(
        risk_score=90,
        risk_level="HIGH",
        risk_reasons=[
            "High probability of synthetic/deepfake audio."
        ],
        fake_score=0.95,
        speaker_mismatch_score=0.90,
        context_risk_score=0.80,
    )

    assert result.action == "BLOCK"
    assert len(result.alerts) >= 1


def test_suspicious_call_hold():

    engine = SecurityDecisionEngine()

    result = engine.decide(
        risk_score=60,
        risk_level="MEDIUM",
        risk_reasons=[],
        fake_score=0.75,
        speaker_mismatch_score=0.20,
        context_risk_score=0.90,
    )

    assert result.action == "HOLD"


def test_medium_risk_warning():

    engine = SecurityDecisionEngine()

    result = engine.decide(
        risk_score=50,
        risk_level="MEDIUM",
        risk_reasons=[],
        fake_score=0.60,
        speaker_mismatch_score=0.20,
        context_risk_score=0.20,
    )

    assert result.action == "WARN"


def test_invalid_risk_score():

    engine = SecurityDecisionEngine()

    with pytest.raises(ValueError):

        engine.decide(
            risk_score=120,
            risk_level="HIGH",
            risk_reasons=[],
            fake_score=0.5,
            speaker_mismatch_score=0.5,
            context_risk_score=0.5,
        )
        