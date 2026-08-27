from pathlib import Path

import numpy as np
import pytest

from app.realtime_engine import RealtimeDetectionEngine


REAL_AUDIO = Path(
    "data/release_in_the_wild/test/real/10004.wav"
)


class FakeDetector:
    """Small fake detector for fast unit testing."""

    def __init__(self):
        self.calls = []

    def predict(self, audio_path):

        self.calls.append(str(audio_path))

        return {
            "prediction": "real",
            "fake_score": 0.10,
            "real_score": 0.90,
            "confidence": 0.90,
        }


def test_realtime_engine_analyzes_chunks():

    detector = FakeDetector()

    engine = RealtimeDetectionEngine(
        detector=detector
    )

    result = engine.analyze(
        REAL_AUDIO
    )

    assert result["total_chunks"] == 2

    assert result["fake_chunks"] == 0
    assert result["real_chunks"] == 2

    assert result["prediction"] == "real"

    assert result["average_fake_score"] == pytest.approx(
        0.10
    )

    assert result["average_real_score"] == pytest.approx(
        0.90
    )

    assert len(result["chunks"]) == 2


def test_realtime_engine_chunk_metadata():

    detector = FakeDetector()

    engine = RealtimeDetectionEngine(
        detector=detector
    )

    result = engine.analyze(
        REAL_AUDIO
    )

    first = result["chunks"][0]

    assert first["chunk_index"] == 0
    assert first["start_time"] == 0.0
    assert first["duration"] == 5.0


def test_realtime_engine_detects_fake_average():

    class FakeDeepfakeDetector:

        def predict(self, audio_path):

            return {
                "prediction": "fake",
                "fake_score": 0.95,
                "real_score": 0.05,
                "confidence": 0.95,
            }

    engine = RealtimeDetectionEngine(
        detector=FakeDeepfakeDetector()
    )

    result = engine.analyze(
        REAL_AUDIO
    )

    assert result["prediction"] == "fake"

    assert result["average_fake_score"] == pytest.approx(
        0.95
    )

    assert result["fake_chunks"] == 2


def test_realtime_engine_missing_file():

    detector = FakeDetector()

    engine = RealtimeDetectionEngine(
        detector=detector
    )

    with pytest.raises(FileNotFoundError):
        engine.analyze(
            "does_not_exist.wav"
        )