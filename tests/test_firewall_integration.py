from pathlib import Path

from app.firewall import VoiceSecurityFirewall


REAL_AUDIO = Path(
    "data/release_in_the_wild/test/real/10004.wav"
)

FAKE_AUDIO = Path(
    "data/release_in_the_wild/test/fake/10012.wav"
)


def test_real_audio_with_matching_reference():
    firewall = VoiceSecurityFirewall()

    result = firewall.analyze_call(
        REAL_AUDIO,
        reference_audio=REAL_AUDIO,
        context_risk_score=0.0,
    )

    assert result["voice_detection"]["prediction"] == "real"

    assert result["speaker_verification"] is not None

    assert result["speaker_verification"]["same_speaker"] is True

    assert result["risk"]["action"] == "ALLOW"


def test_fake_audio_with_real_reference():
    firewall = VoiceSecurityFirewall()

    result = firewall.analyze_call(
        FAKE_AUDIO,
        reference_audio=REAL_AUDIO,
        context_risk_score=0.8,
    )

    assert result["voice_detection"]["prediction"] == "fake"

    assert result["speaker_verification"] is not None

    assert result["speaker_verification"]["same_speaker"] is False

    assert result["risk"]["action"] == "BLOCK"