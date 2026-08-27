import pytest

from notifications.manager import NotificationManager


def test_low_risk_is_not_published():
    manager = NotificationManager()

    assert manager.publish_risk(
        risk_score=20,
        risk_level="LOW",
        action="ALLOW",
    ) is None
    assert manager.list_notifications() == []


def test_medium_risk_creates_warning():
    manager = NotificationManager()

    notification = manager.publish_risk(
        risk_score=48,
        risk_level="MEDIUM",
        action="WARN",
        reasons=["Moderate synthetic voice probability."],
        source="upload:test.wav",
    )

    assert notification is not None
    assert notification["severity"] == "warning"
    assert notification["risk_score"] == 48.0


def test_high_risk_creates_critical_and_deduplicates():
    manager = NotificationManager()
    arguments = {
        "risk_score": 91,
        "risk_level": "HIGH",
        "action": "BLOCK",
        "source": "live-call",
        "chunk_index": 2,
    }

    first = manager.publish_risk(**arguments)
    second = manager.publish_risk(**arguments)

    assert first is not None
    assert first["severity"] == "critical"
    assert second == first
    assert len(manager.list_notifications()) == 1


def test_acknowledge_hides_notification_by_default():
    manager = NotificationManager()
    notification = manager.publish_risk(
        risk_score=50,
        risk_level="MEDIUM",
        action="WARN",
    )

    assert notification is not None
    assert manager.acknowledge(notification["id"]) is True
    assert manager.list_notifications() == []
    assert len(manager.list_notifications(include_acknowledged=True)) == 1
    assert manager.acknowledge(999) is False


def test_invalid_capacity_is_rejected():
    with pytest.raises(ValueError):
        NotificationManager(max_notifications=0)
