import pytest

from app.risk_engine import RiskEngine


def test_low_risk_call():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=0.05,
        speaker_mismatch_score=0.05,
        context_risk_score=0.05,
    )

    assert result.score < 40
    assert result.level == "LOW"
    assert result.action == "ALLOW"


def test_medium_risk_call():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=0.70,
        speaker_mismatch_score=0.20,
        context_risk_score=0.20,
    )

    assert 40 <= result.score < 70
    assert result.level == "MEDIUM"
    assert result.action == "WARN"


def test_high_risk_call():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=0.90,
        speaker_mismatch_score=0.90,
        context_risk_score=0.90,
    )

    assert result.score >= 70
    assert result.level == "HIGH"
    assert result.action == "BLOCK"


def test_context_risk():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=0.10,
        speaker_mismatch_score=0.10,
        context_risk_score=0.90,
    )

    assert result.score > 10
    assert "context" in " ".join(
        result.reasons
    ).lower()


def test_fake_audio_risk():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=1.0,
        speaker_mismatch_score=0.0,
        context_risk_score=0.0,
    )

    assert result.score == 50.0
    assert result.level == "MEDIUM"
    assert result.action == "WARN"


def test_speaker_mismatch_risk():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=0.0,
        speaker_mismatch_score=1.0,
        context_risk_score=0.0,
    )

    assert result.score == 30.0
    assert result.level == "LOW"
    assert result.action == "ALLOW"


def test_invalid_fake_score():
    engine = RiskEngine()

    with pytest.raises(ValueError):
        engine.calculate(
            fake_score=1.5,
            speaker_mismatch_score=0.0,
            context_risk_score=0.0,
        )


def test_invalid_context_score():
    engine = RiskEngine()

    with pytest.raises(ValueError):
        engine.calculate(
            fake_score=0.2,
            speaker_mismatch_score=0.0,
            context_risk_score=-0.1,
        )


def test_invalid_speaker_score():
    engine = RiskEngine()

    with pytest.raises(ValueError):
        engine.calculate(
            fake_score=0.2,
            speaker_mismatch_score=1.5,
            context_risk_score=0.0,
        )


def test_invalid_type():
    engine = RiskEngine()

    with pytest.raises(TypeError):
        engine.calculate(
            fake_score="fake",
            speaker_mismatch_score=0.0,
            context_risk_score=0.0,
        )


def test_weight_normalization():
    engine = RiskEngine(
        fake_weight=5,
        speaker_weight=3,
        context_weight=2,
    )

    result = engine.calculate(
        fake_score=1.0,
        speaker_mismatch_score=0.0,
        context_risk_score=0.0,
    )

    assert result.score == 50.0