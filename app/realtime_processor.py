from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


class RealtimeAudioProcessor:
    """
    Splits an audio file into fixed-duration chunks.

    This simulates real-time call processing:
        complete call
            -> chunk 1
            -> chunk 2
            -> chunk 3
            -> ...

    The chunks can later be replaced by live microphone/
    VoIP audio frames without changing the detection layer.
    """

    TARGET_SAMPLE_RATE = 16000
    DEFAULT_CHUNK_SECONDS = 5.0

    SUPPORTED_FORMATS = {
        ".wav",
        ".flac",
        ".ogg",
        ".mp3",
    }

    def __init__(
        self,
        target_sample_rate: int = TARGET_SAMPLE_RATE,
        chunk_seconds: float = DEFAULT_CHUNK_SECONDS,
    ):
        if target_sample_rate <= 0:
            raise ValueError(
                "target_sample_rate must be greater than zero."
            )

        if chunk_seconds <= 0:
            raise ValueError(
                "chunk_seconds must be greater than zero."
            )

        self.target_sample_rate = target_sample_rate
        self.chunk_seconds = chunk_seconds

    def _validate_path(
        self,
        audio_path: str | Path,
    ) -> Path:
        """Validate the input audio path."""

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
                f"Unsupported audio format: {path.suffix}"
            )

        return path

    def _load_audio(
        self,
        path: Path,
    ) -> np.ndarray:
        """Load audio, convert to mono and resample."""

        try:
            audio, sample_rate = sf.read(
                str(path),
                dtype="float32",
                always_2d=False,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load audio '{path}': {exc}"
            ) from exc

        if audio.size == 0:
            raise ValueError(
                f"Audio file contains no samples: {path}"
            )

        # Convert stereo/multichannel to mono.
        if audio.ndim > 1:
            audio = np.mean(
                audio,
                axis=1,
            )

        audio = audio.astype(
            np.float32,
            copy=False,
        )

        # Resample if necessary.
        if sample_rate != self.target_sample_rate:

            duration = len(audio) / sample_rate

            new_length = int(
                duration * self.target_sample_rate
            )

            if new_length <= 0:
                raise ValueError(
                    f"Audio is too short to resample: {path}"
                )

            old_positions = np.linspace(
                0,
                len(audio) - 1,
                num=len(audio),
            )

            new_positions = np.linspace(
                0,
                len(audio) - 1,
                num=new_length,
            )

            audio = np.interp(
                new_positions,
                old_positions,
                audio,
            ).astype(np.float32)

        return audio

    def split(
        self,
        audio_path: str | Path,
    ) -> list[np.ndarray]:
        """
        Split audio into fixed-duration chunks.

        Returns:
            List of float32 mono chunks at 16 kHz.
        """

        path = self._validate_path(
            audio_path
        )

        audio = self._load_audio(path)

        chunk_samples = int(
            self.target_sample_rate
            * self.chunk_seconds
        )

        if chunk_samples <= 0:
            raise ValueError(
                "Calculated chunk size is invalid."
            )

        chunks: list[np.ndarray] = []

        for start in range(
            0,
            len(audio),
            chunk_samples,
        ):

            end = min(
                start + chunk_samples,
                len(audio),
            )

            chunk = audio[start:end]

            if chunk.size == 0:
                continue

            chunks.append(
                chunk.astype(
                    np.float32,
                    copy=False,
                )
            )

        if not chunks:
            raise ValueError(
                f"No audio chunks generated from: {path}"
            )

        return chunks

    def get_chunk_metadata(
        self,
        audio_path: str | Path,
    ) -> list[dict[str, Any]]:
        """Return timing metadata for each chunk."""

        chunks = self.split(audio_path)

        metadata = []

        for index, chunk in enumerate(chunks):

            start_time = (
                index * self.chunk_seconds
            )

            duration = (
                len(chunk)
                / self.target_sample_rate
            )

            metadata.append(
                {
                    "chunk_index": index,
                    "start_time": start_time,
                    "duration": duration,
                    "samples": len(chunk),
                }
            )

        return metadata