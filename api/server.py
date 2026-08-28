from pathlib import Path
import shutil
import tempfile
import uuid
import json
import subprocess

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.firewall import VoiceSecurityFirewall
from fastapi.responses import StreamingResponse
from fastapi import Body, FastAPI, File, Form, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
import asyncio
import wave

from api.call_simulator import CallSimulator
from app.realtime_engine import RealtimeDetectionEngine
from app.transcription_service import transcribe_audio
from challenge_response import ChallengeService
from notifications import NotificationManager
# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = BASE_DIR / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

FRONTEND_DIR = BASE_DIR / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"

CSS_DIR = FRONTEND_DIR / "css"
JS_DIR = FRONTEND_DIR / "js"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="VoiceShield AI",
    description="AI-Powered Voice Cloning Impersonation Detection Firewall",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC FRONTEND
# ============================================================

app.mount(
    "/css",
    StaticFiles(directory=CSS_DIR),
    name="css",
)

app.mount(
    "/js",
    StaticFiles(directory=JS_DIR),
    name="js",
)


# ============================================================
# FIREWALL
# ============================================================

firewall = None
realtime_engine = None
challenge_service = ChallengeService()
notification_manager = NotificationManager()


def publish_result_notification(
    result: dict,
    source: str,
    chunk_index: int | None = None,
) -> None:
    """Publish a serious result without changing the analysis response."""

    risk = result.get("risk", {})

    if risk or "risk_score" in result:
        notification_manager.publish_risk(
            risk_score=risk.get(
                "score",
                result.get("risk_score", 0),
            ),
            risk_level=risk.get(
                "level",
                result.get("risk_level", "LOW"),
            ),
            action=risk.get(
                "action",
                result.get("action", "ALLOW"),
            ),
            reasons=risk.get(
                "reasons",
                result.get("reasons", []),
            ),
            source=source,
            chunk_index=chunk_index,
        )
        return

    detection = result.get("voice_detection", result)
    fake_score = float(
        detection.get("fake_score", 0) or 0
    )

    if fake_score < 0.40:
        return

    level = "HIGH" if fake_score >= 0.70 else "MEDIUM"
    action = "BLOCK" if level == "HIGH" else "WARN"

    notification_manager.publish_risk(
        risk_score=fake_score * 100,
        risk_level=level,
        action=action,
        reasons=[
            "Serious synthetic voice signal detected in live audio."
        ],
        source=source,
        chunk_index=chunk_index,
    )

@app.on_event("startup")
def startup_event():
    global firewall, realtime_engine

    print("=" * 70)
    print("Initializing VoiceShield AI API")
    print("=" * 70)

    firewall = VoiceSecurityFirewall()
    firewall.challenge_service = challenge_service
    realtime_engine = RealtimeDetectionEngine()
    print("=" * 70)
    print("VoiceShield AI API READY")
    print("=" * 70)


# ============================================================
# FRONTEND ROUTE
# ============================================================

@app.get("/", include_in_schema=False)
def serve_frontend():
    """
    Serve the main VoiceShield AI frontend.
    """

    if not INDEX_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Frontend not found: {INDEX_FILE}",
        )

    return FileResponse(INDEX_FILE)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():

    return {
        "status": "online",
        "service": "VoiceShield AI",
        "firewall": firewall is not None,
    }


@app.get("/api/notifications")
def get_notifications(
    since_id: int = 0,
    include_acknowledged: bool = False,
):
    """Return new serious alerts for browser and mobile clients."""

    return {
        "notifications": notification_manager.list_notifications(
            since_id=since_id,
            include_acknowledged=include_acknowledged,
        )
    }


@app.post("/api/challenge-response/start")
def start_challenge_response():
    """Create a fresh challenge for additional verification."""

    service = getattr(firewall, "challenge_service", challenge_service)
    challenge = service.start_challenge()

    return {
        "challenge_id": challenge["challenge_id"],
        "challenge": challenge["phrase"],
        "expires_at": challenge["expires_at"].isoformat(),
        "max_attempts": 3,
    }


@app.post("/api/challenge-response/verify")
async def verify_challenge_response(
    challenge_id: str = Form(...),
    audio: UploadFile = File(...),
):
    """Verify a spoken challenge response against the challenge phrase and current risk signals."""

    service = getattr(firewall, "challenge_service", challenge_service)

    if not challenge_id:
        raise HTTPException(status_code=400, detail="Missing challenge session identifier.")

    session = service.get_session(challenge_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Challenge session not found.")

    if not audio or not audio.filename:
        raise HTTPException(status_code=400, detail="No audio response was provided.")

    content = await audio.read()
    if not content:
        raise HTTPException(status_code=400, detail="Challenge response audio was empty.")

    extension = Path(audio.filename).suffix.lower() or ".webm"
    temp_path = None
    converted_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        if extension in {".webm", ".m4a", ".aac", ".opus", ".oga"}:
            converted_path = convert_audio_to_wav(temp_path)
            analysis_path = converted_path
        else:
            analysis_path = temp_path

        voice_result = None
        if firewall is not None and hasattr(firewall, "detector"):
            voice_result = firewall.detector.predict(analysis_path)

        transcription = await asyncio.to_thread(
            transcribe_audio,
            content,
            audio.filename,
            audio.content_type or "audio/webm",
        )
        transcript_text = str(transcription.get("transcript", "") or "").strip()

        if voice_result is None:
            result = service.verify_response(
                challenge_id=challenge_id,
                transcript=transcript_text,
                verification_error="Voice authenticity service unavailable for challenge verification.",
            )
        else:
            result = service.verify_response(
                challenge_id=challenge_id,
                transcript=transcript_text,
                voice_prediction=str(voice_result.get("prediction", "")).lower(),
                voice_fake_score=float(voice_result.get("fake_score", 0.0) or 0.0),
                speaker_verified=None,
                speaker_confidence=None,
            )

        return result.to_dict()

    except Exception as exc:
        result = service.verify_response(
            challenge_id=challenge_id,
            transcript="",
            verification_error=str(exc),
        )
        return result.to_dict()

    finally:
        for path in (temp_path, converted_path):
            if path is not None:
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass


@app.post("/api/notifications/{notification_id}/acknowledge")
def acknowledge_notification(notification_id: int):
    """Acknowledge an alert after the client has displayed it."""

    if not notification_manager.acknowledge(notification_id):
        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    return {"success": True, "notification_id": notification_id}


@app.post("/api/notifications/test")
def create_test_notification():
    """Create a clearly labeled warning for local notification testing."""

    notification = notification_manager.publish_risk(
        risk_score=45,
        risk_level="MEDIUM",
        action="WARN",
        reasons=["Notification delivery test event."],
        source=f"manual-test:{uuid.uuid4().hex}",
    )

    return {
        "success": True,
        "notification": notification,
    }


@app.post("/api/notifications/live-final")
def create_live_final_notification(payload: dict = Body(...)):
    """Publish one alert after the browser confirms a stable live result."""

    notification = notification_manager.publish_risk(
        risk_score=payload.get("risk_score", 0),
        risk_level=payload.get("risk_level", "LOW"),
        action=payload.get("action", "ALLOW"),
        reasons=payload.get("reasons", []),
        source=payload.get("source", "microphone-call"),
    )

    return {"success": True, "notification": notification}


# ============================================================
# ANALYZE AUDIO
# ============================================================

@app.post("/api/analyze")
async def analyze_audio(
    file: UploadFile = File(...)
    
):

    if firewall is None:
        raise HTTPException(
            status_code=503,
            detail="VoiceShield AI firewall is still initializing.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided.",
        )

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    allowed_extensions = {
        ".wav",
        ".mp3",
        ".flac",
        ".ogg",
        ".webm",
        ".m4a",
        ".aac",
        ".opus",
        ".oga",
    }

    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Use WAV, MP3, FLAC, OGG, WebM, M4A, AAC, or Opus."
            ),
        )

    # --------------------------------------------------------
    # Temporary file
    # --------------------------------------------------------

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            shutil.copyfileobj(
                file.file,
                temp_file,
            )

            temp_path = Path(
                temp_file.name
            )

        # ----------------------------------------------------
        # Convert browser recordings before running the firewall.
        # ----------------------------------------------------

        analysis_path = temp_path

        if extension in {
            ".webm",
            ".m4a",
            ".aac",
            ".opus",
            ".oga",
        }:
            converted_path = convert_audio_to_wav(temp_path)
            analysis_path = converted_path

        # ----------------------------------------------------
        # Run firewall
        # ----------------------------------------------------

        result = firewall.analyze_call(
            audio_path=analysis_path,
        )

        publish_result_notification(
            result,
            source=f"upload:{uuid.uuid4().hex}",
        )

        return {
            "success": True,
            "filename": file.filename,
            "result": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    finally:

        if temp_path is not None:

            try:
                temp_path.unlink(
                    missing_ok=True
                )
            except Exception:
                pass
def pcm_to_wav(
    pcm_data: bytes,
    output_path: Path,
    sample_rate: int = 16000,
):
    """
    Convert browser PCM16 mono audio into a WAV file.
    """

    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # PCM16
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)

def convert_audio_to_wav(input_path: Path) -> Path:
    """
    Convert browser-recorded audio (WebM/Opus, etc.)
    into a temporary 16 kHz mono WAV file for the
    realtime detection engine.
    """

    output_path = RUNTIME_DIR / f"converted_{uuid.uuid4().hex}.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if process.returncode != 0:
        raise RuntimeError(
            "FFmpeg audio conversion failed:\n"
            + process.stderr[-2000:]
        )

    if not output_path.exists():
        raise RuntimeError(
            "FFmpeg completed but WAV output was not created."
        )

    return output_path

@app.post("/api/simulate-call")
async def simulate_call(
    audio: UploadFile = File(...)
):
    """
    Receive a live browser audio chunk.

    Browser normally sends WebM/Opus.
    Convert it to WAV before passing it to
    the realtime detection engine.
    """

    if firewall is None:
        raise HTTPException(
            status_code=503,
            detail="VoiceShield AI firewall is still initializing.",
        )

    if not audio.filename:
        raise HTTPException(
            status_code=400,
            detail="No audio chunk provided.",
        )

    input_suffix = (
        Path(audio.filename).suffix.lower()
        or ".webm"
    )

    input_path = (
        RUNTIME_DIR
        / f"live_input_{uuid.uuid4().hex}{input_suffix}"
    )

    converted_path = None

    try:

        # ----------------------------------------------------
        # Save browser chunk
        # ----------------------------------------------------

        content = await audio.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Received empty audio chunk.",
            )

        input_path.write_bytes(content)

        transcription = await asyncio.to_thread(
            transcribe_audio,
            content,
            audio.filename,
            audio.content_type or "audio/webm",
        )

        print(
            f"[LIVE] Received chunk: "
            f"{audio.filename} "
            f"({len(content)} bytes)"
        )

        # ----------------------------------------------------
        # Convert WebM/Opus -> WAV
        # ----------------------------------------------------

        converted_path = convert_audio_to_wav(
            input_path
        )

        print(
            f"[LIVE] Converted to WAV: "
            f"{converted_path.name}"
        )

        # ----------------------------------------------------
        # Run realtime detector
        # ----------------------------------------------------

        simulator = CallSimulator()

        events = []

        for event in simulator.stream_call(
            converted_path,
            realtime_delay=False,
        ):
            events.append(event)

        return {
            "success": True,
            "events": events,
            "transcription": transcription,
        }

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "[LIVE] ERROR:",
            repr(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    finally:

        # ----------------------------------------------------
        # Cleanup temporary files
        # ----------------------------------------------------

        try:
            if input_path.exists():
                input_path.unlink()
        except Exception:
            pass

        try:
            if converted_path and converted_path.exists():
                converted_path.unlink()
        except Exception:
            pass

@app.websocket("/ws/live-call")
async def live_call(websocket: WebSocket):
    """
    Real-time microphone detection endpoint.

    Browser sends:
        PCM16 mono audio @ 16 kHz

    Server:
        buffers audio
        analyzes each window
        sends JSON detection events
    """

    await websocket.accept()

    print("LIVE CALL CONNECTED")

    if realtime_engine is None:
        await websocket.send_json({
            "event": "error",
            "message": "Realtime detection engine is not ready."
        })

        await websocket.close()
        return

    audio_buffer = bytearray()

    # 3 seconds of PCM16 mono @ 16 kHz
    SAMPLE_RATE = 16000
    BYTES_PER_SAMPLE = 2
    CHANNELS = 1

    WINDOW_SECONDS = 3

    WINDOW_BYTES = (
        SAMPLE_RATE
        * BYTES_PER_SAMPLE
        * CHANNELS
        * WINDOW_SECONDS
    )

    chunk_index = 0
    session_id = uuid.uuid4().hex

    try:

        await websocket.send_json({
            "event": "live_connected",
            "message": "Live call detection started.",
            "sample_rate": SAMPLE_RATE,
            "window_seconds": WINDOW_SECONDS,
        })

        while True:

            data = await websocket.receive_bytes()

            audio_buffer.extend(data)

            # ------------------------------------------------
            # Analyze whenever we have a complete window
            # ------------------------------------------------

            while len(audio_buffer) >= WINDOW_BYTES:

                window = bytes(
                    audio_buffer[:WINDOW_BYTES]
                )

                del audio_buffer[:WINDOW_BYTES]

                temp_path = (
                    RUNTIME_DIR
                    / f"live_{uuid.uuid4().hex}.wav"
                )

                try:

                    pcm_to_wav(
                        window,
                        temp_path,
                        sample_rate=SAMPLE_RATE,
                    )

                    result = await asyncio.to_thread(
                        realtime_engine.analyze,
                        temp_path,
                    )

                    event = {
                        "event": "live_analysis",
                        "chunk_index": chunk_index,
                        "result": result,
                    }

                    await websocket.send_json(event)

                    chunk_index += 1

                except Exception as exc:

                    await websocket.send_json({
                        "event": "error",
                        "chunk_index": chunk_index,
                        "message": str(exc),
                    })

                finally:

                    temp_path.unlink(
                        missing_ok=True
                    )

    except WebSocketDisconnect:

        print("LIVE CALL DISCONNECTED")

    except Exception as exc:

        print(
            f"LIVE CALL ERROR: {exc}"
        )

        try:

            await websocket.send_json({
                "event": "error",
                "message": str(exc),
            })

        except Exception:
            pass