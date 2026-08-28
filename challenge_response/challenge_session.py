from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ChallengeSessionState(str, Enum):
    CREATED = "CREATED"
    WAITING_FOR_RESPONSE = "WAITING_FOR_RESPONSE"
    PROCESSING = "PROCESSING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


@dataclass
class ChallengeSession:
    challenge_id: str
    phrase: str
    created_at: datetime
    expires_at: datetime
    max_attempts: int = 3
    attempt_count: int = 0
    state: ChallengeSessionState = ChallengeSessionState.CREATED
    response_transcript: str | None = None
    challenge_verification_result: dict[str, Any] | None = None
    last_error: str | None = None

    def mark_waiting_for_response(self) -> None:
        self.state = ChallengeSessionState.WAITING_FOR_RESPONSE

    def mark_processing(self) -> None:
        self.state = ChallengeSessionState.PROCESSING

    def mark_verified(self) -> None:
        self.state = ChallengeSessionState.VERIFIED

    def mark_failed(self) -> None:
        self.state = ChallengeSessionState.FAILED

    def mark_expired(self) -> None:
        self.state = ChallengeSessionState.EXPIRED

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def can_attempt(self) -> bool:
        if self.is_expired():
            self.state = ChallengeSessionState.EXPIRED
            return False

        if self.state in {
            ChallengeSessionState.FAILED,
            ChallengeSessionState.VERIFIED,
            ChallengeSessionState.EXPIRED,
        }:
            return False

        return self.attempt_count < self.max_attempts

    def record_attempt(self) -> bool:
        if not self.can_attempt():
            return False

        self.attempt_count += 1

        if self.attempt_count >= self.max_attempts:
            self.state = ChallengeSessionState.FAILED
            return False

        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "phrase": self.phrase,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "state": self.state.value,
            "response_transcript": self.response_transcript,
            "challenge_verification_result": self.challenge_verification_result,
        }
