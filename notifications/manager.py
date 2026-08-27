from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any


class NotificationManager:
    """Keep a bounded, process-local feed of serious security alerts."""

    def __init__(self, max_notifications: int = 100) -> None:
        if max_notifications < 1:
            raise ValueError("max_notifications must be positive.")

        self._notifications: deque[dict[str, Any]] = deque(
            maxlen=max_notifications,
        )
        self._next_id = 1
        self._lock = Lock()

    def publish_risk(
        self,
        risk_score: float,
        risk_level: str,
        action: str,
        reasons: list[str] | None = None,
        source: str = "voice-analysis",
        chunk_index: int | None = None,
    ) -> dict[str, Any] | None:
        """Publish only MEDIUM/HIGH risk events as warning/critical alerts."""

        score = float(risk_score or 0.0)
        level = str(risk_level or "LOW").upper()
        normalized_action = str(action or "ALLOW").upper()

        if level not in {"MEDIUM", "HIGH"} and normalized_action not in {
            "WARN",
            "HOLD",
            "BLOCK",
        }:
            return None

        severity = "critical" if level == "HIGH" or normalized_action in {
            "HOLD",
            "BLOCK",
        } else "warning"

        title = (
            "Critical voice-security threat"
            if severity == "critical"
            else "Voice-security warning"
        )
        detail = "; ".join(reasons or [])
        if not detail:
            detail = f"Risk score {score:.0f}; action {normalized_action}."

        message = f"{detail} Risk score {score:.0f}. Action: {normalized_action}."
        event_key = f"{source}:{chunk_index if chunk_index is not None else 'call'}"

        with self._lock:
            for existing in self._notifications:
                if existing["event_key"] == event_key:
                    return existing

            notification = {
                "id": self._next_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "severity": severity,
                "title": title,
                "message": message,
                "source": source,
                "event_key": event_key,
                "risk_score": round(score, 2),
                "risk_level": level,
                "action": normalized_action,
                "chunk_index": chunk_index,
                "acknowledged": False,
            }
            self._next_id += 1
            self._notifications.append(notification)
            return notification

    def list_notifications(
        self,
        since_id: int = 0,
        include_acknowledged: bool = False,
    ) -> list[dict[str, Any]]:
        """Return notifications newer than since_id in chronological order."""

        with self._lock:
            return [
                notification.copy()
                for notification in self._notifications
                if notification["id"] > since_id
                and (
                    include_acknowledged
                    or not notification["acknowledged"]
                )
            ]

    def acknowledge(self, notification_id: int) -> bool:
        """Mark one notification as acknowledged."""

        with self._lock:
            for notification in self._notifications:
                if notification["id"] == notification_id:
                    notification["acknowledged"] = True
                    return True
        return False
