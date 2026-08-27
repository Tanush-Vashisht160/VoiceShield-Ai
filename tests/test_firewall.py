from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.firewall import VoiceSecurityFirewall


@pytest.fixture
def mock_firewall_deps():
    """Mock all subsystem dependencies initialized inside VoiceSecurityFirewall."""
    with patch("app.firewall.DeepfakeDetector") as mock_det, \
         patch("app.firewall.RealtimeDetectionEngine") as mock_rt, \
         patch("app.firewall.SpeakerVerifier") as mock_spk, \
         patch("app.firewall.RiskEngine") as mock_risk, \
         patch("app.firewall.ContextAnalyzer") as mock_ctx:

        # Setup standard return objects for mocks
        detector_instance = mock_det.return_value
        detector_instance.predict.return_value = {
            "prediction": "REAL",
            "fake_score": 0.1,
            "real_score": 0.9,
            "confidence": 0.9,
        }

        realtime_instance = mock_rt.return_value
        realtime_instance.analyze.return_value = {
            "prediction": "REAL",
            "average_fake_score": 0.15,
            "average_real_score": 0.85,
            "confidence": 0.85,
        }

        speaker_instance = mock_spk.return_value
        speaker_instance.verify.return_value = {
            "verified": True,
            "score": 0.90,  # 0.90 similarity -> 0.10 mismatch
        }

        risk_instance = mock_risk.return_value
        mock_risk_obj = MagicMock()
        mock_risk_obj.score = 0.2
        mock_risk_obj.level = "LOW"
        mock_risk_obj.action = "ALLOW"
        mock_risk_obj.reasons = []
        risk_instance.calculate.return_value = mock_risk_obj

        context_instance = mock_ctx.return_value
        context_instance.analyze.return_value = {
            "score": 0.80,
            "level": "HIGH",
            "action": "BLOCK",
            "matched_categories": ["otp"],
        }

        yield {
            "detector": detector_instance,
            "realtime": realtime_instance,
            "speaker": speaker_instance,
            "risk": risk_instance,
            "context": context_instance,
        }


@pytest.fixture
def dummy_audio_file(tmp_path: Path) -> Path:
    """Create a temporary valid audio file for testing."""
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"dummy audio data")
    return audio_file


@pytest.fixture
def dummy_reference_file(tmp_path: Path) -> Path:
    """Create a temporary valid reference audio file for testing."""
    ref_file = tmp_path / "ref.wav"
    ref_file.write_bytes(b"dummy ref audio data")
    return ref_file


# ---------------------------------------------------------------------------
# Input Path & Score Validation Tests
# ---------------------------------------------------------------------------

def test_analyze_call_missing_audio_file():
    firewall = VoiceSecurityFirewall()
    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        firewall.analyze_call("non_existent_file.wav")


def test_analyze_call_directory_as_audio(tmp_path: Path):
    firewall = VoiceSecurityFirewall()
    with pytest.raises(ValueError, match="is a directory"):
        firewall.analyze_call(tmp_path)


def test_analyze_call_missing_reference_file(dummy_audio_file: Path):
    firewall = VoiceSecurityFirewall()
    with pytest.raises(FileNotFoundError, match="Reference audio file not found"):
        firewall.analyze_call(dummy_audio_file, reference_audio="non_existent_ref.wav")


@pytest.mark.parametrize("invalid_score", [-0.1, 1.1, "not_a_number"])
def test_invalid_score_validation(dummy_audio_file: Path, invalid_score):
    firewall = VoiceSecurityFirewall()

    with pytest.raises(ValueError):
        firewall.analyze_call(dummy_audio_file, context_risk_score=invalid_score)

    with pytest.raises(ValueError):
        firewall.analyze_call(dummy_audio_file, speaker_mismatch_score=invalid_score)


# ---------------------------------------------------------------------------
# Workflow & Pipeline Integration Tests
# ---------------------------------------------------------------------------

def test_analyze_call_realtime_mode(mock_firewall_deps, dummy_audio_file: Path):
    firewall = VoiceSecurityFirewall()
    result = firewall.analyze_call(dummy_audio_file, realtime=True)

    mock_firewall_deps["realtime"].analyze.assert_called_once_with(dummy_audio_file)
    mock_firewall_deps["detector"].predict.assert_not_called()
    assert result["risk_inputs"]["fake_score"] == 0.15


def test_analyze_call_non_realtime_mode(mock_firewall_deps, dummy_audio_file: Path):
    firewall = VoiceSecurityFirewall()
    result = firewall.analyze_call(dummy_audio_file, realtime=False)

    mock_firewall_deps["detector"].predict.assert_called_once_with(dummy_audio_file)
    mock_firewall_deps["realtime"].analyze.assert_not_called()
    assert result["risk_inputs"]["fake_score"] == 0.10


def test_transcript_context_analyzer_integration(mock_firewall_deps, dummy_audio_file: Path):
    firewall = VoiceSecurityFirewall()
    transcript = "Please share your OTP code."

    result = firewall.analyze_call(dummy_audio_file, transcript=transcript)

    mock_firewall_deps["context"].analyze.assert_called_once_with(transcript)
    assert result["context_analysis"]["matched_categories"] == ["otp"]
    assert result["risk_inputs"]["context_risk_score"] == 0.80


def test_manual_context_risk_overrides_transcript(mock_firewall_deps, dummy_audio_file: Path):
    firewall = VoiceSecurityFirewall()

    result = firewall.analyze_call(
        dummy_audio_file,
        transcript="Please give me your OTP",
        context_risk_score=0.30,
    )

    # Context analyzer runs, but explicitly provided score takes priority
    mock_firewall_deps["context"].analyze.assert_called_once()
    assert result["risk_inputs"]["context_risk_score"] == 0.30


def test_speaker_verification_mismatch_calculation(
    mock_firewall_deps, dummy_audio_file: Path, dummy_reference_file: Path
):
    firewall = VoiceSecurityFirewall()

    result = firewall.analyze_call(
        dummy_audio_file,
        reference_audio=dummy_reference_file,
    )

    mock_firewall_deps["speaker"].verify.assert_called_once_with(
        dummy_reference_file, dummy_audio_file
    )
    # Speaker similarity score is 0.90 -> expected mismatch is 1.0 - 0.90 = 0.10
    assert result["risk_inputs"]["speaker_mismatch_score"] == pytest.approx(0.10)