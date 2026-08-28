from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import CHALLENGE_RESPONSE_TTL_MINUTES, DEFAULT_CHALLENGE_COLORS, DEFAULT_CHALLENGE_WORDS


class ChallengeGenerator:
    """Generate unpredictable spoken authentication phrases."""

    def __init__(
        self,
        ttl_minutes: int = CHALLENGE_RESPONSE_TTL_MINUTES,
        colors: tuple[str, ...] = DEFAULT_CHALLENGE_COLORS,
        words: tuple[str, ...] = DEFAULT_CHALLENGE_WORDS,
    ) -> None:
        self.ttl_minutes = ttl_minutes
        self.colors = colors
        self.words = words

    def generate(self) -> dict[str, Any]:
        number = secrets.randbelow(100)
        color = secrets.choice(self.colors)
        word = secrets.choice(self.words)

        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(minutes=self.ttl_minutes)

        return {
            "challenge_id": uuid.uuid4().hex,
            "phrase": f"{number} {color} {word}",
            "number": number,
            "color": color,
            "word": word,
            "created_at": created_at,
            "expires_at": expires_at,
        }
