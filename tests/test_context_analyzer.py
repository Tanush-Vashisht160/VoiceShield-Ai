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
    assert result["matched_categories"] == []
    assert result["intent"]["primary_intent"] == "none"


def test_otp_request_is_detected(analyzer):
    result = analyzer.analyze(
        "Please tell me the OTP you received."
    )

    assert result["score"] > 0
    assert "otp_request" in result["matched_categories"]
    assert result["intent"]["primary_intent"] == "otp_disclosure"


def test_financial_request_is_detected(analyzer):
    result = analyzer.analyze(
        "Please transfer the money to this UPI account."
    )

    assert result["score"] > 0
    assert "financial" in result["matched_categories"]
    assert result["intent"]["primary_intent"] == "financial_transfer"


def test_credential_request_is_detected(analyzer):
    result = analyzer.analyze(
        "Tell me your password and CVV."
    )

    assert result["score"] > 0
    assert "credential_request" in result["matched_categories"]
    assert result["intent"]["primary_intent"] == "credential_disclosure"


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


def test_authority_impersonation(analyzer):
    result = analyzer.analyze(
        "I am calling from the bank. "
        "Your account needs verification."
    )

    assert "authority_impersonation" in result[
        "matched_categories"
    ]


def test_urgency_is_detected(analyzer):
    result = analyzer.analyze(
        "You must do this immediately."
    )

    assert "urgency" in result["matched_categories"]
    assert result["score"] > 0


def test_threat_is_detected(analyzer):
    result = analyzer.analyze(
        "If you do not cooperate, the police will arrest you."
    )

    assert "threat_or_fear" in result[
        "matched_categories"
    ]


def test_secrecy_is_detected(analyzer):
    result = analyzer.analyze(
        "Do not tell anyone about this."
    )

    assert "secrecy_or_isolation" in result[
        "matched_categories"
    ]


def test_link_or_software_risk(analyzer):
    result = analyzer.analyze(
        "Click the link and install the application."
    )

    assert "link_or_software" in result[
        "matched_categories"
    ]

    assert result["intent"]["primary_intent"] in {
        "link_interaction",
        "software_installation",
    }


def test_multiple_signals_increase_evidence(analyzer):
    low = analyzer.analyze(
        "Please send the money."
    )

    high = analyzer.analyze(
        "This is urgent. "
        "I am calling from the bank. "
        "Give me the OTP immediately "
        "and transfer the money. "
        "Do not tell anyone."
    )

    assert high["score"] > low["score"]
    assert len(high["signals"]) > len(low["signals"])


def test_empty_text(analyzer):
    result = analyzer.analyze("")

    assert result["score"] == 0.0
    assert result["action"] == "ALLOW"
    assert result["intent"]["primary_intent"] == "none"


def test_invalid_input(analyzer):
    with pytest.raises(TypeError):
        analyzer.analyze(None)