from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification


class DeepfakeDetector:
    """
    Local audio deepfake detector using:

        Vansh180/deepfake-audio-wav2vec2

    Labels:
        bonafide = real
        spoof    = fake/deepfake
    """

    MODEL_NAME = "Vansh180/deepfake-audio-wav2vec2"
    TARGET_SR = 16000

    def __init__(self):
        print(f"Loading deepfake detector: {self.MODEL_NAME}")
        print("Loading audio feature extractor...")

        self.feature_extractor = AutoFeatureExtractor.from_pretrained(
            self.MODEL_NAME
        )

        print("Loading audio classification model...")

        self.model = AutoModelForAudioClassification.from_pretrained(
            self.MODEL_NAME
        )

        self.model.eval()

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model.to(self.device)

        print(f"Detector device: {self.device}")

        # Get labels from model configuration.
        self.id2label = {
            int(k): v
            for k, v in self.model.config.id2label.items()
        }

        print(f"Detector labels: {self.id2label}")
        print("Deepfake detector loaded successfully.")

    def _load_audio(self, audio_path):
        """
        Load audio as mono float32 at 16 kHz.
        """

        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        waveform, sample_rate = sf.read(
            str(audio_path),
            dtype="float32",
            always_2d=False,
        )

        # Convert stereo/multichannel -> mono.
        if waveform.ndim > 1:
            waveform = np.mean(waveform, axis=1)

        waveform = waveform.astype(np.float32)

        # Resample if required.
        if sample_rate != self.TARGET_SR:
            try:
                import torchaudio

                tensor = torch.from_numpy(waveform)

                resampled = torchaudio.functional.resample(
                    tensor,
                    orig_freq=sample_rate,
                    new_freq=self.TARGET_SR,
                )

                waveform = resampled.numpy().astype(np.float32)

            except Exception as exc:
                raise RuntimeError(
                    f"Audio is {sample_rate} Hz but the detector requires "
                    f"{self.TARGET_SR} Hz. Resampling failed: {exc}"
                ) from exc

        return waveform

    def predict(self, audio_path):
        """
        Predict whether an audio file is real or fake.

        Returns:
            {
                "prediction": "real" or "fake",
                "fake_score": float,
                "real_score": float,
                "confidence": float
            }
        """

        waveform = self._load_audio(audio_path)

        inputs = self.feature_extractor(
            waveform,
            sampling_rate=self.TARGET_SR,
            return_tensors="pt",
            padding=True,
        )

        # Move tensors to model device.
        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.no_grad():
            outputs = self.model(**inputs)

            probabilities = torch.softmax(
                outputs.logits,
                dim=-1,
            )[0]

        # Read labels robustly.
        labels = {
            idx: str(label).lower()
            for idx, label in self.id2label.items()
        }

        real_index = None
        fake_index = None

        for idx, label in labels.items():

            if any(
                word in label
                for word in [
                    "bonafide",
                    "bona-fide",
                    "real",
                    "genuine",
                ]
            ):
                real_index = idx

            if any(
                word in label
                for word in [
                    "spoof",
                    "fake",
                    "deepfake",
                    "synthetic",
                ]
            ):
                fake_index = idx

        # Fallback for binary classifier.
        if real_index is None or fake_index is None:

            if len(probabilities) != 2:
                raise RuntimeError(
                    f"Expected binary classifier but model has "
                    f"{len(probabilities)} output classes."
                )

            # The model's label_map/config should normally identify
            # these correctly. This fallback is only used if labels
            # are unavailable.
            real_index = 0
            fake_index = 1

        real_score = float(probabilities[real_index].item())
        fake_score = float(probabilities[fake_index].item())

        prediction = (
            "fake"
            if fake_score >= real_score
            else "real"
        )

        confidence = max(
            real_score,
            fake_score,
        )

        return {
            "prediction": prediction,
            "fake_score": fake_score,
            "real_score": real_score,
            "confidence": confidence,
        }

    # Compatibility with code that may call detect().
    def detect(self, audio_path):
        return self.predict(audio_path)