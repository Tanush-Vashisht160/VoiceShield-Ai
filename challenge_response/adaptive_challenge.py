from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Claim:
    """
    A factual claim extracted from the caller's conversation.
    """

    text: str
    claim_type: str
    subject: str
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "claim_type": self.claim_type,
            "subject": self.subject,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class AdaptiveChallenge:
    """
    A context-aware verification challenge generated from
    a claim made during the conversation.
    """

    challenge_id: str
    claim: Claim
    question: str
    follow_up_question: str
    challenge_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "claim": self.claim.to_dict(),
            "question": self.question,
            "follow_up_question": self.follow_up_question,
            "challenge_type": self.challenge_type,
        }


@dataclass
class ConsistencyResult:
    """
    Result of evaluating an answer against the original claim.
    """

    relevance_score: float
    consistency_score: float
    contradiction_score: float
    confidence: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relevance_score": round(self.relevance_score, 4),
            "consistency_score": round(self.consistency_score, 4),
            "contradiction_score": round(self.contradiction_score, 4),
            "confidence": round(self.confidence, 4),
            "reasons": self.reasons,
        }


class ClaimExtractor:
    """
    Lightweight rule-based claim extractor.

    This intentionally avoids an external LLM dependency.

    It extracts useful claims that can be turned into
    verification questions.
    """

    LOCATION_PATTERNS = [
        r"\bi am at ([^.?!]+)",
        r"\bi'm at ([^.?!]+)",
        r"\bi am in ([^.?!]+)",
        r"\bi'm in ([^.?!]+)",
        r"\bi am currently at ([^.?!]+)",
        r"\bi'm currently at ([^.?!]+)",
        r"\bcurrently at ([^.?!]+)",
    ]

    PERSON_PATTERNS = [
        r"\b([A-Z][a-z]+) is with me\b",
        r"\bmy ([a-z]+) is with me\b",
        r"\bi am with my ([a-z]+)\b",
    ]

    ACTIVITY_PATTERNS = [
        r"\bi am ([a-z]+ing)\b",
        r"\bi'm ([a-z]+ing)\b",
        r"\bi am currently ([a-z]+ing)\b",
        r"\bi'm currently ([a-z]+ing)\b",
    ]

    TIME_PATTERNS = [
        r"\bi will be there in ([^.?!]+)",
        r"\bi am leaving in ([^.?!]+)",
        r"\bi reached ([^.?!]+) ago",
    ]

    @staticmethod
    def _clean(value: str) -> str:
        value = value.strip()
        value = re.sub(r"\s+", " ", value)
        return value.strip(" ,")

    def extract(self, text: str) -> list[Claim]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        if not text.strip():
            return []

        claims: list[Claim] = []

        for pattern in self.LOCATION_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)

            if match:
                subject = self._clean(match.group(1))

                if subject:
                    claims.append(
                        Claim(
                            text=match.group(0).strip(),
                            claim_type="location",
                            subject=subject,
                            confidence=0.90,
                        )
                    )

        for pattern in self.PERSON_PATTERNS:
            match = re.search(pattern, text)

            if match:
                subject = self._clean(match.group(1))

                if subject:
                    claims.append(
                        Claim(
                            text=match.group(0).strip(),
                            claim_type="person",
                            subject=subject,
                            confidence=0.82,
                        )
                    )

        for pattern in self.ACTIVITY_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)

            if match:
                subject = self._clean(match.group(1))

                if subject:
                    claims.append(
                        Claim(
                            text=match.group(0).strip(),
                            claim_type="activity",
                            subject=subject,
                            confidence=0.75,
                        )
                    )

        for pattern in self.TIME_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)

            if match:
                subject = self._clean(match.group(1))

                if subject:
                    claims.append(
                        Claim(
                            text=match.group(0).strip(),
                            claim_type="time",
                            subject=subject,
                            confidence=0.75,
                        )
                    )

        # Remove duplicate claims.
        unique: dict[tuple[str, str], Claim] = {}

        for claim in claims:
            key = (
                claim.claim_type,
                claim.subject.lower(),
            )
            unique[key] = claim

        return list(unique.values())


class AdaptiveChallengeGenerator:
    """
    Generate a verification question from a conversational claim.
    """

    LOCATION_QUESTIONS = (
        "Which terminal, gate, or specific area are you currently at?",
        "What is the nearest visible landmark or sign around you?",
        "What is the closest counter, entrance, or facility to you?",
    )

    PERSON_QUESTIONS = (
        "Who is currently with you and what are they doing?",
        "What is the person with you doing right now?",
        "Where is that person relative to you?",
    )

    ACTIVITY_QUESTIONS = (
        "What did you do immediately before that?",
        "What are you going to do immediately after that?",
        "What is the next thing you need to do?",
    )

    TIME_QUESTIONS = (
        "What happened immediately before that?",
        "What are you planning to do after that?",
        "Why are you following that timing?",
    )

    GENERIC_QUESTIONS = (
        "What can you see immediately around you?",
        "What were you doing immediately before this call?",
        "What are you going to do next?",
    )

    def __init__(
        self,
        claim_extractor: ClaimExtractor | None = None,
    ) -> None:
        self.claim_extractor = claim_extractor or ClaimExtractor()

    @staticmethod
    def _select(options: tuple[str, ...]) -> str:
        return secrets.choice(options)

    def generate_from_claim(
        self,
        claim: Claim,
    ) -> AdaptiveChallenge:

        if claim.claim_type == "location":
            question = self._select(self.LOCATION_QUESTIONS)
            follow_up = self._select(
                (
                    "What is the closest sign, counter, or shop to you?",
                    "What did you pass immediately before reaching that area?",
                    "What are you planning to do after leaving that area?",
                )
            )

        elif claim.claim_type == "person":
            question = self._select(self.PERSON_QUESTIONS)
            follow_up = self._select(
                (
                    "What did that person say to you most recently?",
                    "What were they doing before you answered?",
                    "Where were you both immediately before this?",
                )
            )

        elif claim.claim_type == "activity":
            question = self._select(self.ACTIVITY_QUESTIONS)
            follow_up = self._select(
                (
                    "What happened immediately before that activity?",
                    "What are you going to do after that?",
                    "Why are you doing that right now?",
                )
            )

        elif claim.claim_type == "time":
            question = self._select(self.TIME_QUESTIONS)
            follow_up = self._select(
                (
                    "What caused that timing?",
                    "What happened immediately before that?",
                    "What will happen immediately after that?",
                )
            )

        else:
            question = self._select(self.GENERIC_QUESTIONS)
            follow_up = self._select(self.GENERIC_QUESTIONS)

        challenge_id = secrets.token_hex(16)

        return AdaptiveChallenge(
            challenge_id=challenge_id,
            claim=claim,
            question=question,
            follow_up_question=follow_up,
            challenge_type=claim.claim_type,
        )

    def generate(
        self,
        transcript: str,
    ) -> AdaptiveChallenge | None:

        claims = self.claim_extractor.extract(transcript)

        if not claims:
            return None

        # Prefer the highest-confidence claim.
        claim = max(
            claims,
            key=lambda item: item.confidence,
        )

        return self.generate_from_claim(claim)


class ResponseConsistencyEvaluator:
    """
    Evaluate whether an answer remains consistent with the
    claim and conversation context.

    This is deliberately conservative.

    It does NOT claim that an answer proves identity.
    It only produces a consistency signal.
    """

    CONTRADICTION_PATTERNS = (
        r"\bnot\b",
        r"\bno\b",
        r"\bactually\b",
        r"\bi am not\b",
        r"\bi'm not\b",
        r"\bwrong\b",
        r"\bincorrect\b",
        r"\bnowhere\b",
    )

    @staticmethod
    def _tokens(text: str) -> set[str]:
        words = re.findall(
            r"\b[a-z0-9]+\b",
            text.lower(),
        )

        stop_words = {
            "the",
            "a",
            "an",
            "i",
            "am",
            "is",
            "are",
            "at",
            "in",
            "on",
            "to",
            "of",
            "and",
            "my",
            "me",
            "currently",
            "right",
            "now",
        }

        return {
            word
            for word in words
            if word not in stop_words
        }

    def evaluate(
        self,
        claim: Claim,
        answer: str,
        follow_up_answer: str | None = None,
    ) -> ConsistencyResult:

        if not isinstance(answer, str):
            raise TypeError("answer must be a string")

        answer = answer.strip()

        if not answer:
            return ConsistencyResult(
                relevance_score=0.0,
                consistency_score=0.0,
                contradiction_score=1.0,
                confidence=0.0,
                reasons=["No answer was provided."],
            )

        claim_tokens = self._tokens(claim.subject)
        answer_tokens = self._tokens(answer)

        overlap = 0.0

        if claim_tokens:
            overlap = len(
                claim_tokens.intersection(answer_tokens)
            ) / len(claim_tokens)

        contradiction = any(
            re.search(pattern, answer.lower())
            for pattern in self.CONTRADICTION_PATTERNS
        )

        relevance_score = min(
            1.0,
            0.45 + (0.35 * overlap),
        )

        if len(answer_tokens) >= 2:
            relevance_score += 0.10

        relevance_score = min(
            1.0,
            relevance_score,
        )

        contradiction_score = 1.0 if contradiction else 0.0

        consistency_score = (
            relevance_score * 0.70
            + (1.0 - contradiction_score) * 0.30
        )

        reasons: list[str] = []

        if contradiction:
            reasons.append(
                "The response contains language suggesting a contradiction."
            )
        else:
            reasons.append(
                "The response does not contain an obvious contradiction."
            )

        if len(answer_tokens) >= 2:
            reasons.append(
                "The caller provided a substantive response."
            )
        else:
            reasons.append(
                "The response contains very little contextual information."
            )

        if follow_up_answer:
            follow_tokens = self._tokens(follow_up_answer)

            if len(follow_tokens) >= 2:
                consistency_score += 0.05
                reasons.append(
                    "A substantive follow-up response was provided."
                )

        consistency_score = max(
            0.0,
            min(1.0, consistency_score),
        )

        confidence = (
            consistency_score * 0.65
            + relevance_score * 0.35
        )

        return ConsistencyResult(
            relevance_score=relevance_score,
            consistency_score=consistency_score,
            contradiction_score=contradiction_score,
            confidence=max(
                0.0,
                min(1.0, confidence),
            ),
            reasons=reasons,
        )