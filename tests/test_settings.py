from config.settings import (
    APP_NAME,
    APP_VERSION,
    MODEL_NAME,
    FAKE_THRESHOLD,
    HIGH_RISK_THRESHOLD,
    CRITICAL_RISK_THRESHOLD,
)


def test_settings():

    assert APP_NAME
    assert APP_VERSION
    assert MODEL_NAME

    assert 0.0 <= FAKE_THRESHOLD <= 1.0
    assert 0.0 <= HIGH_RISK_THRESHOLD <= 1.0
    assert 0.0 <= CRITICAL_RISK_THRESHOLD <= 1.0

    assert (
        FAKE_THRESHOLD
        < HIGH_RISK_THRESHOLD
        < CRITICAL_RISK_THRESHOLD
    )