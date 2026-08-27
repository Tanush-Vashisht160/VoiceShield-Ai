from pathlib import Path

import pytest

from api.call_simulator import CallSimulator


class FakeEngine:
    def analyze(self, audio_path):

        return {
            "prediction": "real",

            "total_chunks": 2,

            "average_fake_score": 0.01,

            "average_real_score": 0.99,

            "maximum_fake_score": 0.02,

            "confidence": 0.99,

            "chunks": [
                {
                    "chunk_index": 0,
                    "start_time": 0.0,
                    "duration": 5.0,
                    "prediction": "real",
                    "fake_score": 0.01,
                    "real_score": 0.99,
                    "confidence": 0.99,
                },
                {
                    "chunk_index": 1,
                    "start_time": 5.0,
                    "duration": 3.0,
                    "prediction": "real",
                    "fake_score": 0.02,
                    "real_score": 0.98,
                    "confidence": 0.98,
                },
            ],
        }


def test_simulator_generates_chunk_events(tmp_path):

    audio = tmp_path / "call.wav"

    audio.write_bytes(b"dummy")

    simulator = CallSimulator(
        engine=FakeEngine()
    )

    events = list(
        simulator.stream_call(
            audio,
            realtime_delay=False,
        )
    )

    assert len(events) == 3

    assert events[0]["event"] == "chunk_analysis"

    assert events[0]["chunk_index"] == 0

    assert events[0]["prediction"] == "real"

    assert events[0]["risk_level"] == "LOW"

    assert events[1]["chunk_index"] == 1

    assert events[1]["progress"] == 100.0

    assert events[-1]["event"] == "call_complete"


def test_simulator_detects_high_risk(tmp_path):

    audio = tmp_path / "fake.wav"

    audio.write_bytes(b"dummy")

    class FakeEngine:

        def analyze(self, audio_path):

            return {
                "prediction": "fake",
                "chunks": [
                    {
                        "chunk_index": 0,
                        "start_time": 0.0,
                        "duration": 3.0,
                        "prediction": "fake",
                        "fake_score": 0.95,
                        "real_score": 0.05,
                        "confidence": 0.95,
                    }
                ],
                "average_fake_score": 0.95,
                "average_real_score": 0.05,
                "maximum_fake_score": 0.95,
                "confidence": 0.95,
            }

    simulator = CallSimulator(
        engine=FakeEngine()
    )

    events = list(
        simulator.stream_call(
            audio,
            realtime_delay=False,
        )
    )

    assert events[0]["risk_score"] == 95.0

    assert events[0]["risk_level"] == "HIGH"

    assert events[0]["action"] == "BLOCK"


def test_missing_audio():

    simulator = CallSimulator(
        engine=FakeEngine()
    )

    with pytest.raises(FileNotFoundError):

        list(
            simulator.stream_call(
                "does_not_exist.wav",
                realtime_delay=False,
            )
        )