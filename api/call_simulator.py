from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Generator

from app.realtime_engine import RealtimeDetectionEngine


class CallSimulator:
    """
    Simulates a live phone call from a prerecorded WAV file.

    The audio is processed chunk-by-chunk and yields an event
    after every chunk so the frontend can display a live analysis.
    """

    def __init__(
        self,
        engine: RealtimeDetectionEngine | None = None,
    ):
        self.engine = engine or RealtimeDetectionEngine()

    def stream_call(
        self,
        audio_path: str | Path,
        realtime_delay: bool = True,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Process a recorded call as if it were happening live.

        Args:
            audio_path:
                WAV/audio file to analyze.

            realtime_delay:
                If True, wait approximately the chunk duration
                between events. Useful for demonstrations.

        Yields:
            One event per audio chunk.
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

        result = self.engine.analyze(path)

        chunks = result.get("chunks", [])

        if not chunks:
            raise RuntimeError(
                "Realtime engine returned no audio chunks."
            )

        total_chunks = len(chunks)

        for index, chunk in enumerate(chunks):

            fake_score = float(
                chunk.get("fake_score", 0.0)
            )

            real_score = float(
                chunk.get("real_score", 1.0 - fake_score)
            )

            prediction = chunk.get(
                "prediction",
                "real",
            )

            # ------------------------------------------------------
            # Basic chunk-level risk.
            #
            # Phase 1 intentionally uses the existing deepfake
            # signal. Speaker/context integration comes later.
            # ------------------------------------------------------

            risk_score = round(
                fake_score * 100.0,
                2,
            )

            if risk_score >= 70:
                risk_level = "HIGH"
                action = "BLOCK"

            elif risk_score >= 40:
                risk_level = "MEDIUM"
                action = "WARN"

            else:
                risk_level = "LOW"
                action = "ALLOW"

            event = {
                "event": "chunk_analysis",

                "chunk_index": index,

                "total_chunks": total_chunks,

                "timestamp": float(
                    chunk.get("start_time", 0.0)
                ),

                "duration": float(
                    chunk.get("duration", 0.0)
                ),

                "prediction": prediction,

                "fake_score": round(
                    fake_score,
                    6,
                ),

                "real_score": round(
                    real_score,
                    6,
                ),

                "confidence": round(
                    float(
                        chunk.get(
                            "confidence",
                            max(
                                fake_score,
                                real_score,
                            ),
                        )
                    ),
                    6,
                ),

                "risk_score": risk_score,

                "risk_level": risk_level,

                "action": action,

                "progress": round(
                    ((index + 1) / total_chunks) * 100,
                    2,
                ),
            }

            yield event

            # ------------------------------------------------------
            # Simulate passage of call time.
            #
            # Keep this OFF during automated tests.
            # ------------------------------------------------------

            if realtime_delay:

                duration = float(
                    chunk.get("duration", 0.0)
                )

                # Do not make the demo painfully slow.
                delay = min(
                    max(duration, 0.25),
                    5.0,
                )

                time.sleep(delay)

        # ----------------------------------------------------------
        # Final event
        # ----------------------------------------------------------

        yield {
            "event": "call_complete",

            "total_chunks": total_chunks,

            "prediction": result.get(
                "prediction",
                "unknown",
            ),

            "average_fake_score": round(
                float(
                    result.get(
                        "average_fake_score",
                        0.0,
                    )
                ),
                6,
            ),

            "average_real_score": round(
                float(
                    result.get(
                        "average_real_score",
                        0.0,
                    )
                ),
                6,
            ),

            "maximum_fake_score": round(
                float(
                    result.get(
                        "maximum_fake_score",
                        0.0,
                    )
                ),
                6,
            ),

            "confidence": round(
                float(
                    result.get(
                        "confidence",
                        0.0,
                    )
                ),
                6,
            ),
        }