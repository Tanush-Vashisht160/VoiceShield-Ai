from unittest import result

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
        fake_availability=1.0,
        speaker_availability=1.0,
        context_availability=1.0,
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
        fake_availability=1.0,
        speaker_availability=1.0,
        context_availability=1.0,
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
        fake_availability=1.0,
        speaker_availability=0.0,
        context_availability=0.0,
    )

    assert result.score == 100.0
    assert result.level == "HIGH"
    assert result.action == "BLOCK"


def test_speaker_mismatch_risk():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=0.0,
        speaker_mismatch_score=1.0,
        context_risk_score=0.0,
        fake_availability=1.0,
        speaker_availability=1.0,
        context_availability=0.0,
    )

    assert result.score > 0
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

    assert result.score == 100.0
    assert result.level == "HIGH"
    assert result.action == "BLOCK"


def test_only_fake_evidence_uses_available_weight():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=1.0,
        speaker_mismatch_score=0.0,
        context_risk_score=0.0,
        fake_availability=1.0,
        speaker_availability=0.0,
        context_availability=0.0,
    )

    assert result.score == 100.0
    assert result.level == "HIGH"
    assert result.action == "BLOCK"


def test_missing_evidence_is_not_treated_as_positive_evidence():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=0.10,
        speaker_mismatch_score=0.0,
        context_risk_score=0.0,
        fake_availability=1.0,
        speaker_availability=0.0,
        context_availability=0.0,
    )

    assert result.score == 10.0


def test_all_available_signals_use_original_weights():
    engine = RiskEngine()

    result = engine.calculate(
        fake_score=0.90,
        speaker_mismatch_score=0.80,
        context_risk_score=0.70,
        fake_availability=1.0,
        speaker_availability=1.0,
        context_availability=1.0,
    )

    assert result.score > 70
    assert result.level == "HIGH"
    assert result.action == "BLOCK"


def test_multiple_high_risk_signals_have_corroboration():
    engine = RiskEngine()

    base = engine.calculate(
        fake_score=0.80,
        speaker_mismatch_score=0.80,
        context_risk_score=0.80,
        fake_availability=1.0,
        speaker_availability=1.0,
        context_availability=1.0,
    )

    assert base.score > 80
    assert any(
        "corroborate" in reason.lower()
        for reason in base.reasons
    )


def test_invalid_availability():
    engine = RiskEngine()

    with pytest.raises(ValueError):
        engine.calculate(
            fake_score=0.5,
            fake_availability=1.5,
        )


def test_no_available_signal_is_rejected():
    engine = RiskEngine()

    with pytest.raises(ValueError):
        engine.calculate(
            fake_score=0.5,
            fake_availability=0.0,
            speaker_availability=0.0,
            context_availability=0.0,
        )