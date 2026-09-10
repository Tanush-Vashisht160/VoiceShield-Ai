import pytest

from app.context_analyzer import ContextAnalyzer


@pytest.fixture
def analyzer():
    return ContextAnalyzer()


def test_safe_conversation(analyzer):
    result = analyzer.analyze(
        "Hello, how are you? "
        "I am calling to discuss the meeting tomorrow."
    )

    assert result["score"] == 0.0
    assert result["level"] == "LOW"
    assert result["action"] == "ALLOW"


def test_otp_request_is_detected(analyzer):
    result = analyzer.analyze(
        "Please tell me the OTP you received."
    )

    assert result["score"] > 0
    assert "otp" in result["matched_categories"]


def test_financial_request_is_detected(analyzer):
    result = analyzer.analyze(
        "Please transfer the money to this UPI account."
    )

    assert result["score"] > 0
    assert "financial" in result["matched_categories"]


def test_credential_request_is_detected(analyzer):
    result = analyzer.analyze(
        "Tell me your password and CVV."
    )

    assert result["score"] > 0
    assert "credentials" in result["matched_categories"]


def test_high_risk_scam_context(analyzer):
    result = analyzer.analyze(
        "This is urgent. "
        "Your account will be blocked immediately. "
        "Please give me the OTP and password "
        "and transfer the money right now."
    )

    assert result["score"] >= 0.70
    assert result["level"] == "HIGH"
    assert result["action"] == "BLOCK"


def test_empty_text(analyzer):
    result = analyzer.analyze("")

    assert result["score"] == 0.0
    assert result["action"] == "ALLOW"


def test_invalid_input(analyzer):
    with pytest.raises(TypeError):
        analyzer.analyze(None)