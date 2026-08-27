from pathlib import Path

from app.speaker_verifier import SpeakerVerifier


REAL_DIR = Path("data/release_in_the_wild/train/real")

REAL_FILES = sorted(REAL_DIR.glob("*.wav"))


def test_speaker_verifier_loads():
    verifier = SpeakerVerifier()

    assert verifier is not None


def test_speaker_verification_runs():
    assert len(REAL_FILES) >= 2, (
        f"Need at least 2 real audio files in {REAL_DIR}"
    )

    verifier = SpeakerVerifier()

    result = verifier.verify(
        REAL_FILES[0],
        REAL_FILES[1],
    )

    assert "same_speaker" in result
    assert "score" in result

    assert isinstance(
        result["same_speaker"],
        bool,
    )

    assert isinstance(
        result["score"],
        float,
    )