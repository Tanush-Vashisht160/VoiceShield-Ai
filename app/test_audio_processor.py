from pathlib import Path

import numpy as np

from app.audio_processor import AudioProcessor


DATASET_ROOT = Path("data/release_in_the_wild")

REAL_AUDIO = DATASET_ROOT / "test" / "real" / "10004.wav"
FAKE_AUDIO = DATASET_ROOT / "test" / "fake" / "10012.wav"


def test_audio_processor():
    processor = AudioProcessor()

    print("=" * 70)
    print("AUDIO PROCESSOR TEST")
    print("=" * 70)

    for label, audio_path in [
        ("REAL", REAL_AUDIO),
        ("FAKE", FAKE_AUDIO),
    ]:
        print(f"\n[{label}]")
        print(f"File: {audio_path}")

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Test audio does not exist: {audio_path}"
            )

        audio, sample_rate = processor.load(audio_path)

        duration = processor.get_duration(audio)

        print(f"Sample rate : {sample_rate} Hz")
        print(f"Samples     : {len(audio)}")
        print(f"Duration    : {duration:.3f} sec")
        print(f"Dtype       : {audio.dtype}")
        print(
            f"Range       : [{audio.min():.4f}, {audio.max():.4f}]"
        )

        assert sample_rate == 16_000
        assert audio.dtype == np.float32
        assert len(audio) > 0
        assert np.all(np.isfinite(audio))
        assert np.max(np.abs(audio)) <= 1.0 + 1e-6
        assert duration <= 30.0

    print("\n" + "=" * 70)
    print("AUDIO PROCESSOR TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    test_audio_processor()