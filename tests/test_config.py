from config.settings import settings


def test_application_name():
    assert settings.app_name == "VoiceShield AI"


def test_environment():
    assert settings.app_env == "development"