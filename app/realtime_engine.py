from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from app.detector import DeepfakeDetector
from app.realtime_processor import RealtimeAudioProcessor


class RealtimeDetectionEngine:
    """
    Near-real-time voice deepfake analysis engine.

    Pipeline:

        Audio file
            ↓
        5-second chunks
            ↓
        AntiDeepfake detector
            ↓
        Chunk-level predictions
            ↓
        Aggregated call-level prediction
    """

    def __init__(
        self,
        detector: DeepfakeDetector | None = None,
        processor: RealtimeAudioProcessor | None = None,
    ):
        self.detector = (
            detector
            if detector is not None
            else DeepfakeDetector()
        )

        self.processor = (
            processor
            if processor is not None
            else RealtimeAudioProcessor(
                chunk_seconds=5.0
            )
        )

    def _save_chunk(
        self,
        chunk: np.ndarray,
        output_path: Path,
    ) -> None:
        """Save a single audio chunk as 16-kHz mono WAV."""

        if chunk.size == 0:
            raise ValueError(
                "Cannot save an empty audio chunk."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            sf.write(
                str(output_path),
                chunk.astype(np.float32),
                self.processor.target_sample_rate,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to save audio chunk "
                f"'{output_path}': {exc}"
            ) from exc

    def analyze(
        self,
        audio_path: str | Path,
    ) -> dict[str, Any]:
        """
        Analyze an audio file chunk-by-chunk.

        Returns a complete call-level analysis.
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

        chunks = self.processor.split(path)
        metadata = self.processor.get_chunk_metadata(path)

        if len(chunks) != len(metadata):
            raise RuntimeError(
                "Chunk and metadata counts do not match."
            )

        results: list[dict[str, Any]] = []

        # Temporary directory for detector input chunks.
        chunk_directory = (
            Path("data") / "runtime_chunks"
        )

        chunk_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for index, chunk in enumerate(chunks):

            chunk_path = (
                chunk_directory
                / f"{path.stem}_chunk_{index}.wav"
            )

            self._save_chunk(
                chunk,
                chunk_path,
            )

            try:
                detection = self.detector.predict(
                    chunk_path
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Deepfake detection failed "
                    f"for chunk {index}: {exc}"
                ) from exc

            chunk_info = {
                "chunk_index": index,
                "start_time": metadata[index][
                    "start_time"
                ],
                "duration": metadata[index][
                    "duration"
                ],
                "audio_file": str(chunk_path),
                "prediction": detection[
                    "prediction"
                ],
                "fake_score": detection[
                    "fake_score"
                ],
                "real_score": detection[
                    "real_score"
                ],
                "confidence": detection[
                    "confidence"
                ],
            }

            results.append(chunk_info)

        if not results:
            raise RuntimeError(
                "No chunk detection results were produced."
            )

        # ------------------------------------------------------------
        # Aggregate chunk predictions.
        # ------------------------------------------------------------

        fake_scores = [
            result["fake_score"]
            for result in results
        ]

        real_scores = [
            result["real_score"]
            for result in results
        ]

        average_fake_score = float(
            np.mean(fake_scores)
        )

        average_real_score = float(
            np.mean(real_scores)
        )

        maximum_fake_score = float(
            np.max(fake_scores)
        )

        fake_chunk_count = sum(
            result["prediction"] == "fake"
            for result in results
        )

        real_chunk_count = sum(
            result["prediction"] == "real"
            for result in results
        )

        # A call is considered suspicious when the
        # average fake probability is >= 0.50.
        call_prediction = (
            "fake"
            if average_fake_score >= 0.50
            else "real"
        )

        call_confidence = max(
            average_fake_score,
            average_real_score,
        )

        return {
            "audio_file": str(path),
            "total_chunks": len(results),
            "fake_chunks": fake_chunk_count,
            "real_chunks": real_chunk_count,
            "average_fake_score": average_fake_score,
            "average_real_score": average_real_score,
            "maximum_fake_score": maximum_fake_score,
            "prediction": call_prediction,
            "confidence": call_confidence,
            "chunks": results,
        }