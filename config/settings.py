import os

from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# ============================================================
# APPLICATION SETTINGS
# ============================================================

APP_NAME = os.getenv(
    "APP_NAME",
    "Voice Security Firewall",
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0",
)

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
)

DEBUG = os.getenv(
    "DEBUG",
    "False",
).lower() == "true"


# ============================================================
# MODEL SETTINGS
# ============================================================

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "MelodyMachine/Deepfake-audio-detection-V2",
)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ElevenLabs_API_KEY")


# ============================================================
# RISK SETTINGS
# ============================================================

FAKE_THRESHOLD = float(
    os.getenv(
        "FAKE_THRESHOLD",
        "0.50",
    )
)

HIGH_RISK_THRESHOLD = float(
    os.getenv(
        "HIGH_RISK_THRESHOLD",
        "0.75",
    )
)

CRITICAL_RISK_THRESHOLD = float(
    os.getenv(
        "CRITICAL_RISK_THRESHOLD",
        "0.90",
    )
)


# ============================================================
# SETTINGS OBJECT
# ============================================================

class Settings:
    app_name = APP_NAME
    app_version = APP_VERSION
    app_env = APP_ENV
    debug = DEBUG

    model_name = MODEL_NAME

    sarvam_api_key = SARVAM_API_KEY
    elevenlabs_api_key = ELEVENLABS_API_KEY

    fake_threshold = FAKE_THRESHOLD
    high_risk_threshold = HIGH_RISK_THRESHOLD
    critical_risk_threshold = CRITICAL_RISK_THRESHOLD

    hf_token = os.getenv("HF_TOKEN")


settings = Settings()

# Backward-compatible module-level HF_TOKEN
HF_TOKEN = settings.hf_token