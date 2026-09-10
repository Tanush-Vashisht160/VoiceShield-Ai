import pytest

from app.intent_analyzer import IntentAnalyzer


@pytest.fixture
def analyzer():
    return IntentAnalyzer()


def test_safe_conversation(analyzer):
    result = analyzer.analyze(
        "Hello, how are you? "
        "I am calling to discuss the meeting tomorrow."
    )

    assert result["primary_intent"] == "none"
    assert result["confidence"] == 0.0
    assert result["evidence"] == []


def test_otp_intent(analyzer):
    result = analyzer.analyze(
        "Please tell me the OTP you received."
    )

    assert result["primary_intent"] == "otp_disclosure"
    assert result["confidence"] > 0.0


def test_financial_transfer_intent(analyzer):
    result = analyzer.analyze(
        "Please transfer the money to this UPI account."
    )

    assert result["primary_intent"] == "financial_transfer"
    assert result["confidence"] > 0.0


def test_credential_intent(analyzer):
    result = analyzer.analyze(
        "Tell me your password and CVV."
    )

    assert result["primary_intent"] == "credential_disclosure"
    assert result["confidence"] > 0.0


def test_multiple_intents(analyzer):
    result = analyzer.analyze(
        "Give me the OTP and transfer the money immediately."
    )

    assert result["primary_intent"] in {
        "otp_disclosure",
        "financial_transfer",
    }

    assert len(result["secondary_intents"]) >= 1
    assert result["confidence"] > 0.0


def test_link_intent(analyzer):
    result = analyzer.analyze(
        "Click the link I have sent you."
    )

    assert result["primary_intent"] == "link_interaction"


def test_software_installation_intent(analyzer):
    result = analyzer.analyze(
        "Download and install this remote desktop application."
    )

    assert result["primary_intent"] == "software_installation"


def test_invalid_input(analyzer):
    with pytest.raises(TypeError):
        analyzer.analyze(None)


def test_empty_input(analyzer):
    result = analyzer.analyze("")

    assert result["primary_intent"] == "none"
    assert result["confidence"] == 0.0