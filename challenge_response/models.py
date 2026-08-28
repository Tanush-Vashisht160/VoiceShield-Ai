from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ChallengeAuthenticationResult:
    challenge_id: str
    challenge_passed: bool
    challenge_confidence: float | None = None
    speaker_verified: bool | None = None
    speaker_confidence: float | None = None
    voice_authentic: bool | None = None
    voice_confidence: float | None = None
    final_status: str = "INCONCLUSIVE"
    risk_score: float = 0.0
    recommendation: str = "Exercise caution and use an alternate verification method."
    reasons: list[str] = field(default_factory=list)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "challenge_passed": self.challenge_passed,
            "challenge_confidence": self.challenge_confidence,
            "speaker_verified": self.speaker_verified,
            "speaker_confidence": self.speaker_confidence,
            "voice_authentic": self.voice_authentic,
            "voice_confidence": self.voice_confidence,
            "status": self.final_status,
            "final_status": self.final_status,
            "risk_score": self.risk_score,
            "recommendation": self.recommendation,
            "reasons": self.reasons,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
