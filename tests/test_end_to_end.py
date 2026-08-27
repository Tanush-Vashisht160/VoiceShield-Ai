from pathlib import Path

from app.firewall import VoiceSecurityFirewall


REAL_AUDIO = Path(
    "data/release_in_the_wild/test/real/10004.wav"
)

FAKE_AUDIO = Path(
    "data/release_in_the_wild/test/fake/10012.wav"
)


def test_real_call_is_allowed():
    firewall = VoiceSecurityFirewall()

    result = firewall.analyze_call(
        audio_path=REAL_AUDIO,
        reference_audio=REAL_AUDIO,
        context_risk_score=0.0,
        realtime=True,
    )

    assert result["voice_detection"]["prediction"] == "real"

    assert result["speaker_verification"] is not None
    assert result["speaker_verification"]["same_speaker"] is True

    assert result["risk"]["action"] == "ALLOW"


def test_fake_call_is_blocked():
    firewall = VoiceSecurityFirewall()

    result = firewall.analyze_call(
        audio_path=FAKE_AUDIO,
        reference_audio=REAL_AUDIO,
        context_risk_score=0.8,
        realtime=True,
    )

    assert result["voice_detection"]["prediction"] == "fake"

    assert result["speaker_verification"] is not None
    assert result["speaker_verification"]["same_speaker"] is False

    assert result["risk"]["action"] == "BLOCK"


def test_missing_audio_is_rejected():
    firewall = VoiceSecurityFirewall()

    missing = Path(
        "data/does_not_exist.wav"
    )

    try:
        firewall.analyze_call(missing)
    except FileNotFoundError:
        return

    raise AssertionError(
        "Missing audio should raise FileNotFoundError."
    )


def test_invalid_context_score_is_rejected():
    firewall = VoiceSecurityFirewall()

    try:
        firewall.analyze_call(
            REAL_AUDIO,
            context_risk_score=2.0,
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid context score should raise ValueError."
    )