from pathlib import Path

from app.detector import DeepfakeDetector


REAL_AUDIO = Path(
    "data/release_in_the_wild/test/real/10004.wav"
)

FAKE_AUDIO = Path(
    "data/release_in_the_wild/test/fake/10012.wav"
)


def test_detector_loads():
    detector = DeepfakeDetector()

    assert detector is not None


def test_real_audio_can_be_analyzed():
    detector = DeepfakeDetector()

    result = detector.predict(REAL_AUDIO)

    assert "prediction" in result
    assert "fake_score" in result
    assert "real_score" in result

    assert 0.0 <= result["fake_score"] <= 1.0
    assert 0.0 <= result["real_score"] <= 1.0


def test_fake_audio_can_be_analyzed():
    detector = DeepfakeDetector()

    result = detector.predict(FAKE_AUDIO)

    assert "prediction" in result
    assert "fake_score" in result
    assert "real_score" in result

    assert 0.0 <= result["fake_score"] <= 1.0
    assert 0.0 <= result["real_score"] <= 1.0