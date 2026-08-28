from __future__ import annotations

import re
from typing import Any


class ChallengePhraseVerifier:
    """Verify a spoken challenge phrase with controlled normalization."""

    NUMBER_WORDS = {
        "zero": "0",
        "oh": "0",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
        "eleven": "11",
        "twelve": "12",
        "thirteen": "13",
        "fourteen": "14",
        "fifteen": "15",
        "sixteen": "16",
        "seventeen": "17",
        "eighteen": "18",
        "nineteen": "19",
        "twenty": "20",
        "thirty": "30",
        "forty": "40",
        "fourty": "40",
        "fifty": "50",
        "sixty": "60",
        "seventy": "70",
        "eighty": "80",
        "ninety": "90",
    }

    TENS_WORDS = {"twenty", "thirty", "forty", "fourty", "fifty", "sixty", "seventy", "eighty", "ninety"}

    @staticmethod
    def _normalize_text(value: str | None) -> str:
        if value is None:
            return ""

        normalized = str(value).lower()
        normalized = normalized.replace("-", " ")
        normalized = normalized.replace("_", " ")
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @classmethod
    def _number_like_token(cls, token: str) -> str:
        token = token.strip().lower()
        if token.isdigit():
            return token
        if token in cls.NUMBER_WORDS:
            return cls.NUMBER_WORDS[token]
        return token

    @classmethod
    def normalize_phrase(cls, value: str | None) -> str:
        text = cls._normalize_text(value)
        if not text:
            return ""

        tokens = text.split()
        normalized_tokens: list[str] = []
        index = 0

        while index < len(tokens):
            token = tokens[index]

            if token.isdigit():
                normalized_tokens.append(token)
                index += 1
                continue

            if token in cls.TENS_WORDS and index + 1 < len(tokens):
                next_token = tokens[index + 1]
                if next_token in cls.NUMBER_WORDS:
                    try:
                        next_value = int(cls.NUMBER_WORDS[next_token])
                    except (TypeError, ValueError):
                        next_value = None

                    if next_value is not None and 0 <= next_value <= 9:
                        combined_value = int(cls.NUMBER_WORDS[token]) + next_value
                        normalized_tokens.append(str(combined_value))
                        index += 2
                        continue

            normalized_tokens.append(cls._number_like_token(token))
            index += 1

        return " ".join(normalized_tokens)

    @classmethod
    def verify(cls, expected: str | None, actual: str | None) -> dict[str, Any]:
        expected_normalized = cls.normalize_phrase(expected)
        actual_normalized = cls.normalize_phrase(actual)

        if not expected_normalized or not actual_normalized:
            return {
                "passed": False,
                "confidence": 0.0,
                "normalized_expected": expected_normalized,
                "normalized_actual": actual_normalized,
                "mismatch": "empty transcript or expected phrase",
            }

        if expected_normalized == actual_normalized:
            return {
                "passed": True,
                "confidence": 0.99,
                "normalized_expected": expected_normalized,
                "normalized_actual": actual_normalized,
                "mismatch": None,
            }

        return {
            "passed": False,
            "confidence": 0.0,
            "normalized_expected": expected_normalized,
            "normalized_actual": actual_normalized,
            "mismatch": {
                "expected": expected_normalized,
                "actual": actual_normalized,
            },
        }
