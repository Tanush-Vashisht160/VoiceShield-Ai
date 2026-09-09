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
) -> dict[str, Any]:

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
        payload: Any = json.loads(
            response.read().decode("utf-8")
        )

    if not isinstance(payload, dict):
        return {
            "transcript": "",
            "language_code": None,
            "language_probability": None,
        }

    transcript = (
        payload.get(
            "transcript",
            payload.get("text", ""),
        )
        or ""
    )

    return {
        "transcript": str(transcript).strip(),
        "language_code": payload.get("language_code"),
        "language_probability": payload.get(
            "language_probability"
        ),
    }


def _sarvam_transcribe(
    api_key: str,
    audio: bytes,
    filename: str,
    content_type: str,
) -> dict[str, Any]:

    return _post_transcription(
        SARVAM_URL,
        {"api-subscription-key": api_key},
        {
            "model": "saaras:v3",
            "mode": "transcribe",
            "language_code": "unknown",
        },
        audio,
        filename,
        content_type,
    )


def _sarvam_translate(
    api_key: str,
    audio: bytes,
    filename: str,
    content_type: str,
) -> dict[str, Any]:

    return _post_transcription(
        SARVAM_URL,
        {"api-subscription-key": api_key},
        {
            "model": "saaras:v3",
            "mode": "translate",
            "language_code": "unknown",
        },
        audio,
        filename,
        content_type,
    )


def _elevenlabs_transcribe(
    api_key: str,
    audio: bytes,
    filename: str,
    content_type: str,
) -> dict[str, Any]:

    return _post_transcription(
        ELEVENLABS_URL,
        {"xi-api-key": api_key},
        {
            "model_id": "scribe_v1",
        },
        audio,
        filename,
        content_type,
    )


def transcribe_audio(
    audio: bytes,
    filename: str = "live_chunk.webm",
    content_type: str = "audio/webm",
) -> dict[str, Any]:
    """
    Multilingual transcription with provider fallback.

    Returns:
        {
            "provider": str | None,
            "transcript": str,
            "analysis_transcript": str,
            "language_code": str | None,
            "language_probability": float | None,
            "error": str | None,
        }
    """

    sarvam_key = os.getenv(
        "SARVAM_API_KEY",
        "",
    ).strip()

    elevenlabs_key = os.getenv(
        "ElevenLabs_API_KEY",
        "",
    ).strip()

    last_error = (
        "No transcription API key is configured."
    )

    # ---------------------------------------------------------
    # 1. SARVAM
    # ---------------------------------------------------------

    if sarvam_key:

        try:

            transcription = _sarvam_transcribe(
                sarvam_key,
                audio,
                filename,
                content_type,
            )

            transcript = transcription["transcript"]

            language_code = (
                transcription.get("language_code")
            )

            language_probability = (
                transcription.get(
                    "language_probability"
                )
            )

            # English does not need translation.
            if (
                language_code is None
                or language_code.startswith("en")
            ):

                analysis_transcript = transcript

            else:

                try:

                    translation = _sarvam_translate(
                        sarvam_key,
                        audio,
                        filename,
                        content_type,
                    )

                    analysis_transcript = (
                        translation.get(
                            "transcript",
                            transcript,
                        )
                        or transcript
                    )

                except (
                    error.HTTPError,
                    error.URLError,
                    TimeoutError,
                    OSError,
                    ValueError,
                ) as exc:

                    print(
                        "[TRANSCRIPTION] "
                        f"Translation failed: {exc}"
                    )

                    # Keep original transcript if
                    # translation fails.
                    analysis_transcript = transcript

            return {
                "provider": "sarvam",
                "transcript": transcript,
                "analysis_transcript": analysis_transcript,
                "language_code": language_code,
                "language_probability": language_probability,
                "error": None,
            }

        except (
            error.HTTPError,
            error.URLError,
            TimeoutError,
            OSError,
            ValueError,
        ) as exc:

            last_error = f"sarvam: {exc}"

            print(
                f"[TRANSCRIPTION] {last_error}"
            )

    # ---------------------------------------------------------
    # 2. ELEVENLABS FALLBACK
    # ---------------------------------------------------------

    if elevenlabs_key:

        try:

            transcription = _elevenlabs_transcribe(
                elevenlabs_key,
                audio,
                filename,
                content_type,
            )

            transcript = transcription["transcript"]

            return {
                "provider": "elevenlabs",
                "transcript": transcript,
                "analysis_transcript": transcript,
                "language_code": None,
                "language_probability": None,
                "error": None,
            }

        except (
            error.HTTPError,
            error.URLError,
            TimeoutError,
            OSError,
            ValueError,
        ) as exc:

            last_error = f"elevenlabs: {exc}"

            print(
                f"[TRANSCRIPTION] {last_error}"
            )

    # ---------------------------------------------------------
    # 3. COMPLETE FAILURE
    # ---------------------------------------------------------

    return {
        "provider": None,
        "transcript": "",
        "analysis_transcript": "",
        "language_code": None,
        "language_probability": None,
        "error": last_error,
    }