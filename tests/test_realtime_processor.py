from pathlib import Path

import pytest

from app.realtime_processor import RealtimeAudioProcessor


REAL_AUDIO = Path(
    "data/release_in_the_wild/test/real/10004.wav"
)


def test_realtime_processor_creates_chunks():

    processor = RealtimeAudioProcessor(
        chunk_seconds=5.0
    )

    chunks = processor.split(
        REAL_AUDIO
    )

    assert chunks
    assert all(
        chunk.dtype.name == "float32"
        for chunk in chunks
    )

    assert all(
        len(chunk) > 0
        for chunk in chunks
    )


def test_realtime_processor_metadata():

    processor = RealtimeAudioProcessor(
        chunk_seconds=5.0
    )

    metadata = processor.get_chunk_metadata(
        REAL_AUDIO
    )

    assert metadata

    assert metadata[0]["chunk_index"] == 0
    assert metadata[0]["start_time"] == 0.0

    for item in metadata:
        assert item["duration"] > 0
        assert item["samples"] > 0


def test_invalid_audio_path():

    processor = RealtimeAudioProcessor()

    with pytest.raises(FileNotFoundError):
        processor.split(
            "does_not_exist.wav"
        )


def test_invalid_chunk_size():

    with pytest.raises(ValueError):
        RealtimeAudioProcessor(
            chunk_seconds=0
        )