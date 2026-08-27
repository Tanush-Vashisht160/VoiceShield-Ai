from pathlib import Path

import librosa
import numpy as np


TARGET_SAMPLE_RATE = 16_000
MAX_DURATION_SECONDS = 30.0


class AudioProcessor:
    """Load and normalize audio for the VoiceShield AI pipeline."""

    SUPPORTED_FORMATS = {".wav", ".mp3", ".flac", ".ogg"}

    def __init__(
        self,
        target_sample_rate: int = TARGET_SAMPLE_RATE,
        max_duration: float = MAX_DURATION_SECONDS,
    ):
        if target_sample_rate <= 0:
            raise ValueError("target_sample_rate must be greater than 0.")

        if max_duration <= 0:
            raise ValueError("max_duration must be greater than 0.")

        self.target_sample_rate = target_sample_rate
        self.max_duration = max_duration

    def load(self, audio_path: str | Path) -> tuple[np.ndarray, int]:
        """
        Load audio as mono float32 samples.

        Audio is resampled to target_sample_rate and limited
        to max_duration seconds.
        """

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Audio path is not a file: {path}"
            )

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {path.suffix}. "
                f"Supported formats: {sorted(self.SUPPORTED_FORMATS)}"
            )

        try:
            audio, sample_rate = librosa.load(
                path,
                sr=self.target_sample_rate,
                mono=True,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load audio file '{path}': {exc}"
            ) from exc

        if audio is None or audio.size == 0:
            raise ValueError(
                f"Audio file contains no samples: {path}"
            )

        if not np.all(np.isfinite(audio)):
            raise ValueError(
                f"Audio contains NaN or infinite values: {path}"
            )

        max_samples = int(
            self.target_sample_rate * self.max_duration
        )

        audio = audio[:max_samples]

        peak = float(np.max(np.abs(audio)))

        if peak > 0:
            audio = audio / peak

        return audio.astype(np.float32), self.target_sample_rate

    def get_duration(self, audio: np.ndarray) -> float:
        """Return audio duration in seconds."""

        if audio is None:
            raise ValueError("audio cannot be None.")

        return len(audio) / self.target_sample_rate