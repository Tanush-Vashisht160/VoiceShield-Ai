from __future__ import annotations

import json
import os
import uuid
from typing import Any
from urllib import error, request


SARVAM_URL = "https://api.sarvam.ai/speech-to-text"
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def _multipart_form(
    fields: dict[str, str],
    file_field: str,
    filename: str,
    content_type: str,
    audio: bytes,
) -> tuple[bytes, str]:
    boundary = f"----VoiceShield{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        body.extend(value.encode())
        body.extend(b"\r\n")

    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
    )
    body.extend(audio)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    return bytes(body), f"multipart/form-data; boundary={boundary}"


def _post_transcription(
    url: str,
    headers: dict[str, str],
    fields: dict[str, str],
    audio: bytes,
    filename: str,
    content_type: str,
) -> str:
    body, multipart_type = _multipart_form(
        fields,
        "file",
        filename,
        content_type,
        audio,
    )
    request_headers = {
        **headers,
        "Content-Type": multipart_type,
        "Accept": "application/json",
    }

    http_request = request.Request(
        url,
        data=body,
        headers=request_headers,
        method="POST",
    )

    with request.urlopen(http_request, timeout=30) as response:
        payload: Any = json.loads(response.read().decode("utf-8"))

    transcript = (
        payload.get("transcript", payload.get("text", ""))
        if isinstance(payload, dict)
        else ""
    )
    return str(transcript or "").strip()


def _sarvam_transcribe(
    api_key: str,
    audio: bytes,
    filename: str,
    content_type: str,
) -> str:
    return _post_transcription(
        SARVAM_URL,
        {"api-subscription-key": api_key},
        {"model": "saaras:v3", "mode": "transcribe"},
        audio,
        filename,
        content_type,
    )


def _elevenlabs_transcribe(
    api_key: str,
    audio: bytes,
    filename: str,
    content_type: str,
) -> str:
    return _post_transcription(
        ELEVENLABS_URL,
        {"xi-api-key": api_key},
        {"model_id": "scribe_v1"},
        audio,
        filename,
        content_type,
    )


def transcribe_audio(
    audio: bytes,
    filename: str = "live_chunk.webm",
    content_type: str = "audio/webm",
) -> dict[str, str | None]:
    """Transcribe with either configured provider, falling back to the other."""

    sarvam_key = os.getenv("SARVAM_API_KEY", "").strip()
    elevenlabs_key = os.getenv("ElevenLabs_API_KEY", "").strip()
    providers: list[tuple[str, str, Any]] = []

    if sarvam_key:
        providers.append(
            ("sarvam", sarvam_key, _sarvam_transcribe)
        )
    if elevenlabs_key:
        providers.append(
            ("elevenlabs", elevenlabs_key, _elevenlabs_transcribe)
        )

    last_error = "No transcription API key is configured."

    for provider, api_key, transcriber in providers:
        try:
            transcript = transcriber(
                api_key,
                audio,
                filename,
                content_type,
            )
            return {
                "provider": provider,
                "transcript": transcript,
            }
        except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = f"{provider}: {exc}"
            print(f"[TRANSCRIPTION] {last_error}")

    return {
        "provider": None,
        "transcript": "",
        "error": last_error,
    }
