from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

from speechbrain.inference.speaker import SpeakerRecognition


class SpeakerVerifier:
    """
    Pretrained speaker-verification component.

    Compares two audio samples and estimates whether
    they belong to the same speaker.

    IMPORTANT:
    This does NOT determine whether audio is AI-generated.
    That is the job of DeepfakeDetector.
    """

    MODEL_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"
    TARGET_SAMPLE_RATE = 16000

    def __init__(self):
        print("Loading speaker verification model...")
        print(f"Model: {self.MODEL_SOURCE}")

        try:
            self.model = SpeakerRecognition.from_hparams(
                source=self.MODEL_SOURCE
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to load speaker verification model. "
                f"Original error: {exc}"
            ) from exc

        print("Speaker verification model loaded successfully.")

    def _validate_audio(
        self,
        audio_path: str | Path,
    ) -> Path:
        """Validate an audio file path."""

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Audio path is not a file: {path}"
            )

        if path.suffix.lower() not in {
            ".wav",
            ".flac",
            ".ogg",
            ".mp3",
        }:
            raise ValueError(
                f"Unsupported audio format: {path.suffix}"
            )

        return path

    def _load_audio(
        self,
        path: Path,
    ) -> tuple[torch.Tensor, int]:
        """
        Load audio using SoundFile.

        This avoids:
        - SpeechBrain k2 audio loading
        - torchaudio/TorchCodec dependency
        - Python wave module limitations with float WAV
        """

        try:
            import soundfile as sf

            audio, sample_rate = sf.read(
                str(path),
                dtype="float32",
                always_2d=True,
            )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load audio '{path}': {exc}"
            ) from exc

        # SoundFile:
        #     [time, channels]
        #
        # SpeechBrain:
        #     [channels, time]

        waveform = torch.from_numpy(
            audio.T.copy()
        ).float()

        return waveform, sample_rate

    def _prepare_audio(
        self,
        path: Path,
    ) -> torch.Tensor:
        """
        Load audio, convert to mono, and resample to 16 kHz.

        Returns:
            Tensor with shape [1, time].
        """

        waveform, sample_rate = self._load_audio(path)

        if waveform.numel() == 0:
            raise ValueError(
                f"Audio file is empty: {path}"
            )

        # Convert multi-channel audio to mono.
        if waveform.shape[0] > 1:
            waveform = waveform.mean(
                dim=0,
                keepdim=True,
            )

        # Make sure we have [1, time].
        elif waveform.shape[0] == 1:
            pass

        else:
            raise ValueError(
                f"Audio has no channels: {path}"
            )

        # Resample to 16 kHz without torchaudio.
        if sample_rate != self.TARGET_SAMPLE_RATE:

            new_length = int(
                waveform.shape[-1]
                * self.TARGET_SAMPLE_RATE
                / sample_rate
            )

            if new_length <= 0:
                raise ValueError(
                    f"Audio is too short: {path}"
                )

            waveform = F.interpolate(
                waveform.unsqueeze(0),
                size=new_length,
                mode="linear",
                align_corners=False,
            ).squeeze(0)

        return waveform.float()

    def verify(
        self,
        reference_audio: str | Path,
        test_audio: str | Path,
    ) -> dict[str, Any]:
        """
        Compare two audio files for speaker similarity.

        Returns:
            {
                "same_speaker": bool,
                "score": float,
                "reference_audio": str,
                "test_audio": str,
            }
        """

        reference_path = self._validate_audio(
            reference_audio
        )

        test_path = self._validate_audio(
            test_audio
        )

        try:
            reference_waveform = self._prepare_audio(
                reference_path
            )

            test_waveform = self._prepare_audio(
                test_path
            )

            # [1, time]
            reference_waveform = (
                reference_waveform
                .squeeze(0)
                .unsqueeze(0)
            )

            test_waveform = (
                test_waveform
                .squeeze(0)
                .unsqueeze(0)
            )

            with torch.no_grad():
                score, prediction = (
                    self.model.verify_batch(
                        reference_waveform,
                        test_waveform,
                    )
                )

        except Exception as exc:
            raise RuntimeError(
                "Speaker verification failed. "
                f"Reference='{reference_path}', "
                f"Test='{test_path}'. "
                f"Original error: {exc}"
            ) from exc

        score_value = float(
            score.squeeze().item()
        )

        prediction_value = bool(
            prediction.squeeze().item()
        )

        return {
            "same_speaker": prediction_value,
            "score": score_value,
            "reference_audio": str(
                reference_path
            ),
            "test_audio": str(
                test_path
            ),
        }