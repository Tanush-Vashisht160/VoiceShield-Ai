from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torch.nn.functional as F

from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

from transformers import (
    AutoFeatureExtractor,
    Wav2Vec2Config,
    Wav2Vec2Model,
)


class DeepfakeDetector:
    """
    Official NII AntiDeepfake Wav2Vec2-Large detector.

    Checkpoint:
        SpeechAntiSpoofingBenchmarks/Wav2Vec2-Large-AntiDeepfake

    Backbone:
        facebook/wav2vec2-large-960h-lv60-self

    Official classifier:
        AdaptiveAvgPool1d(1)
        Linear(1024 -> 2)

    Official class ordering:
        0 = fake
        1 = real
    """

    MODEL_NAME = "SpeechAntiSpoofingBenchmarks/Wav2Vec2-Large-AntiDeepfake"
    BACKBONE_NAME = "facebook/wav2vec2-large-960h-lv60-self"

    TARGET_SR = 16000

    def __init__(self):

        print("=" * 70)
        print("Loading official AntiDeepfake detector")
        print("=" * 70)

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        print(f"Checkpoint: {self.MODEL_NAME}")
        print(f"Backbone:   {self.BACKBONE_NAME}")
        print(f"Device:     {self.device}")

        # ============================================================
        # 1. AUDIO FEATURE EXTRACTOR
        # ============================================================

        print("Loading audio feature extractor...")

        self.feature_extractor = AutoFeatureExtractor.from_pretrained(
            self.BACKBONE_NAME
        )

        # ============================================================
        # 2. DOWNLOAD / LOCATE OFFICIAL CHECKPOINT
        # ============================================================

        print("Downloading/loading official AntiDeepfake checkpoint...")

        checkpoint_path = hf_hub_download(
            repo_id=self.MODEL_NAME,
            filename="model.safetensors",
        )

        print("Checkpoint file:")
        print(f"  {checkpoint_path}")

        # ============================================================
        # 3. READ CHECKPOINT
        # ============================================================

        print("Reading official AntiDeepfake checkpoint...")

        checkpoint = load_file(checkpoint_path)

        print(f"Checkpoint tensors: {len(checkpoint)}")

        # ============================================================
        # 4. LOAD WAV2VEC2 CONFIG
        # ============================================================

        print("Loading Wav2Vec2-Large configuration...")

        config = Wav2Vec2Config.from_pretrained(
            self.BACKBONE_NAME
        )

        # Official Fairseq architecture settings.
        config.feat_extract_norm = "layer"
        config.feat_extract_activation = "gelu"

        config.hidden_size = 1024
        config.num_hidden_layers = 24
        config.num_hidden_heads = 16
        config.num_attention_heads = 16
        config.intermediate_size = 4096

        config.conv_dim = [
            512,
            512,
            512,
            512,
            512,
            512,
            512,
        ]

        config.conv_kernel = [
            10,
            3,
            3,
            3,
            3,
            2,
            2,
        ]

        config.conv_stride = [
            5,
            2,
            2,
            2,
            2,
            2,
            2,
        ]

        config.conv_bias = True

        config.num_conv_pos_embeddings = 128
        config.num_conv_pos_embedding_groups = 16

        config.layer_norm_eps = 1e-5

        config.feat_proj_dropout = 0.0
        config.hidden_dropout = 0.0
        config.attention_dropout = 0.0
        config.activation_dropout = 0.0
        config.layerdrop = 0.0

        config.apply_spec_augment = False

        config.do_stable_layer_norm = True

        # ============================================================
        # 5. CREATE WAV2VEC2 BACKBONE
        # ============================================================

        print("Creating Wav2Vec2-Large backbone...")

        self.backbone = Wav2Vec2Model(config)

        # ============================================================
        # 6. CONVERT FAIRSEQ CHECKPOINT -> HUGGINGFACE KEYS
        # ============================================================

        print("Converting official checkpoint keys...")

        converted = {}

        for original_key, value in checkpoint.items():

            key = original_key

            # --------------------------------------------------------
            # Remove Fairseq wrapper.
            # --------------------------------------------------------

            if key.startswith("m_ssl.model."):
                key = key[len("m_ssl.model."):]

            # --------------------------------------------------------
            # Feature extractor convolution layers
            # --------------------------------------------------------

            if key.startswith(
                "feature_extractor.conv_layers."
            ):

                parts = key.split(".")

                layer_number = parts[2]
                component = parts[3]

                # Conv weight/bias
                if component == "0":

                    parameter = parts[4]

                    new_key = (
                        "feature_extractor."
                        f"conv_layers.{layer_number}."
                        f"conv.{parameter}"
                    )

                    converted[new_key] = value
                    continue

                # LayerNorm
                if component == "2":

                    sub_component = parts[4]

                    if sub_component == "1":

                        parameter = parts[5]

                        new_key = (
                            "feature_extractor."
                            f"conv_layers.{layer_number}."
                            f"layer_norm.{parameter}"
                        )

                        converted[new_key] = value
                        continue

            # --------------------------------------------------------
            # Transformer encoder layers
            # --------------------------------------------------------

            if key.startswith("encoder.layers."):

                parts = key.split(".")

                layer_number = parts[2]

                remainder = ".".join(parts[3:])

                remainder = remainder.replace(
                    "self_attn_layer_norm.",
                    "layer_norm."
                )

                remainder = remainder.replace(
                    "self_attn.",
                    "attention."
                )

                remainder = remainder.replace(
                    "fc1.",
                    "feed_forward.intermediate_dense."
                )

                remainder = remainder.replace(
                    "fc2.",
                    "feed_forward.output_dense."
                )

                new_key = (
                    f"encoder.layers.{layer_number}."
                    f"{remainder}"
                )

                converted[new_key] = value
                continue

            # --------------------------------------------------------
            # Encoder final layer norm
            # --------------------------------------------------------

            if key.startswith("encoder.layer_norm."):

                parameter = key.split(".")[-1]

                converted[
                    f"encoder.layer_norm.{parameter}"
                ] = value

                continue

            # --------------------------------------------------------
            # Positional convolution
            # --------------------------------------------------------

            if key.startswith("encoder.pos_conv.0."):

                parameter = key.split(".")[-1]

                converted[
                    f"encoder.pos_conv_embed.conv.{parameter}"
                ] = value

                continue

            # --------------------------------------------------------
            # Feature projection
            #
            # Fairseq:
            #     post_extract_proj.*
            #
            # HF:
            #     feature_projection.projection.*
            # --------------------------------------------------------

            if key.startswith("post_extract_proj."):

                parameter = key.split(".")[-1]

                converted[
                    f"feature_projection.projection.{parameter}"
                ] = value

                continue

            # --------------------------------------------------------
            # Feature projection layer norm
            #
            # Fairseq:
            #     layer_norm.*
            #
            # HF:
            #     feature_projection.layer_norm.*
            # --------------------------------------------------------

            if key.startswith("layer_norm."):

                parameter = key.split(".")[-1]

                converted[
                    f"feature_projection.layer_norm.{parameter}"
                ] = value

                continue

            # --------------------------------------------------------
            # Mask embedding
            # --------------------------------------------------------

            if key == "mask_emb":

                converted[
                    "masked_spec_embed"
                ] = value

                continue

            # --------------------------------------------------------
            # Ignore Fairseq pretraining-only parameters.
            # --------------------------------------------------------

            if key.startswith("quantizer."):
                continue

            if key.startswith("project_q."):
                continue

            if key.startswith("final_proj."):
                continue

            # --------------------------------------------------------
            # Official classifier.
            #
            # DO NOT load it into the Wav2Vec2 backbone.
            #
            # We load it separately below.
            # --------------------------------------------------------

            if key.startswith("proj_fc."):

                parameter = key.split(".")[-1]

                converted[
                    f"proj_fc.{parameter}"
                ] = value

                continue

        print(f"Converted tensors: {len(converted)}")

        # ============================================================
        # 7. LOAD BACKBONE WEIGHTS
        # ============================================================

        backbone_state = {
            key: value
            for key, value in converted.items()
            if not key.startswith("proj_fc.")
        }

        print("Loading converted Wav2Vec2 weights...")

        missing, unexpected = self.backbone.load_state_dict(
            backbone_state,
            strict=False,
        )

        print(
            f"Backbone missing tensors:    {len(missing)}"
        )

        print(
            f"Backbone unexpected tensors: {len(unexpected)}"
        )

        if missing:

            print("\nMissing tensors:")

            for key in missing:
                print(f"  {key}")

        if unexpected:

            print("\nUnexpected tensors:")

            for key in unexpected:
                print(f"  {key}")

        # ============================================================
        # 8. BACKBONE MUST BE COMPLETE
        # ============================================================

        if missing or unexpected:

            raise RuntimeError(
                "\nOfficial AntiDeepfake backbone was not "
                "loaded completely."
            )

        # ============================================================
        # 9. CREATE OFFICIAL CLASSIFICATION HEAD
        # ============================================================

        print("Creating official classification head...")

        self.pool = torch.nn.AdaptiveAvgPool1d(1)

        self.classifier = torch.nn.Linear(
            1024,
            2,
        )

        # ============================================================
        # 10. LOAD proj_fc WEIGHTS
        # ============================================================

        classifier_state = {
            "weight": converted["proj_fc.weight"],
            "bias": converted["proj_fc.bias"],
        }

        classifier_missing, classifier_unexpected = (
            self.classifier.load_state_dict(
                classifier_state,
                strict=True,
            )
        )

        print(
            "Official classifier loaded successfully."
        )

        print(
            "Classifier: AdaptiveAvgPool1d(1) + "
            "Linear(1024 -> 2)"
        )

        print("Class 0: fake")
        print("Class 1: real")

        # ============================================================
        # 11. MOVE MODEL TO DEVICE
        # ============================================================

        self.backbone.to(self.device)
        self.pool.to(self.device)
        self.classifier.to(self.device)

        self.backbone.eval()
        self.pool.eval()
        self.classifier.eval()

        print()
        print("=" * 70)
        print("Official AntiDeepfake detector loaded successfully.")
        print("=" * 70)

    # ================================================================
    # AUDIO LOADING
    # ================================================================

    def _load_audio(self, audio_path):

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

        # Stereo/multichannel -> mono
        if waveform.ndim > 1:

            waveform = np.mean(
                waveform,
                axis=1,
            )

        waveform = waveform.astype(
            np.float32
        )

        # Resample to 16 kHz
        if sample_rate != self.TARGET_SR:

            import torchaudio

            tensor = torch.from_numpy(
                waveform
            )

            tensor = torchaudio.functional.resample(
                tensor,
                orig_freq=sample_rate,
                new_freq=self.TARGET_SR,
            )

            waveform = tensor.numpy().astype(
                np.float32
            )

        # Official inference preprocessing.
        waveform = torch.from_numpy(
            waveform
        )

        waveform = F.layer_norm(
            waveform,
            waveform.shape,
        )

        return waveform

    # ================================================================
    # PREDICTION
    # ================================================================

    def predict(self, audio_path):

        waveform = self._load_audio(
            audio_path
        )

        # Feature extractor is used to ensure the
        # audio preprocessing is compatible with Wav2Vec2.
        #
        # We still pass the normalized waveform to the
        # backbone because the official inference pipeline
        # operates directly on the waveform.

        inputs = self.feature_extractor(
            waveform.numpy(),
            sampling_rate=self.TARGET_SR,
            return_tensors="pt",
            padding=True,
        )

        input_values = inputs.input_values.to(
            self.device
        )

        attention_mask = None

        if "attention_mask" in inputs:

            attention_mask = inputs.attention_mask.to(
                self.device
            )

        with torch.no_grad():

            outputs = self.backbone(
                input_values=input_values,
                attention_mask=attention_mask,
                output_hidden_states=False,
                return_dict=True,
            )

            # [batch, time, hidden]
            embeddings = outputs.last_hidden_state

            # [batch, hidden, time]
            embeddings = embeddings.transpose(
                1,
                2,
            )

            # [batch, hidden, 1]
            pooled = self.pool(
                embeddings
            )

            # [batch, hidden]
            pooled = pooled.squeeze(
                -1
            )

            # [batch, 2]
            logits = self.classifier(
                pooled
            )

            probabilities = torch.softmax(
                logits,
                dim=-1,
            )[0]

        # ============================================================
        # OFFICIAL CLASS ORDER
        #
        # 0 = fake
        # 1 = real
        # ============================================================

        fake_score = float(
            probabilities[0].item()
        )

        real_score = float(
            probabilities[1].item()
        )

        prediction = (
            "fake"
            if fake_score >= real_score
            else "real"
        )

        confidence = max(
            fake_score,
            real_score,
        )

        return {
            "prediction": prediction,
            "fake_score": fake_score,
            "real_score": real_score,
            "confidence": confidence,
        }

    # Compatibility with existing code.
    def detect(self, audio_path):

        return self.predict(audio_path)