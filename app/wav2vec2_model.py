import torch
import torch.nn as nn
from transformers import Wav2Vec2Model as HFWav2Vec2Model


class Wav2Vec2Model(nn.Module):
    """
    Local implementation of the Wav2Vec2 anti-spoofing model
    used by caa-speech-detection-asvspoof2019/wav2vec2-v2-unfrozen.

    Output:
        logits[:, 0] = bonafide
        logits[:, 1] = spoof
    """

    def __init__(self, config: dict):
        super().__init__()

        self.target_samples = config.get(
            "target_samples",
            64000,
        )

        self.hidden_dim = config.get(
            "hidden_dim",
            256,
        )

        self.dropout_probability = config.get(
            "dropout",
            0.1,
        )

        pretrained_model = config.get(
            "pretrained_model",
            "facebook/wav2vec2-base",
        )

        freeze_encoder = config.get(
            "freeze_encoder",
            True,
        )

        freeze_last_n = config.get(
            "freeze_last_n",
            4,
        )

        self.encoder = HFWav2Vec2Model.from_pretrained(
            pretrained_model
        )

        hidden_size = self.encoder.config.hidden_size

        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, self.hidden_dim),
            nn.GELU(),
            nn.Dropout(self.dropout_probability),
            nn.Linear(self.hidden_dim, 2),
        )

        if freeze_encoder:
            for parameter in self.encoder.parameters():
                parameter.requires_grad = False

            if freeze_last_n > 0:
                layers = self.encoder.encoder.layers

                for layer in layers[-freeze_last_n:]:
                    for parameter in layer.parameters():
                        parameter.requires_grad = True

                for parameter in self.encoder.encoder.layer_norm.parameters():
                    parameter.requires_grad = True

    def forward(self, inputs: dict) -> dict:
        waveform = inputs["frames"]

        outputs = self.encoder(
            input_values=waveform,
            attention_mask=None,
        )

        hidden_states = outputs.last_hidden_state

        pooled = hidden_states.mean(dim=1)

        logits = self.classifier(pooled)

        return {
            "logits": logits,
        }