# Challenge–Response Voice Authentication

This module adds a layered verification step for suspicious or high-risk calls. It is intentionally isolated from the existing VoiceShield live-call flow and does not replace the current deepfake or risk logic.

> Challenge-response authentication is a layered defense and does not make voice cloning impossible.

## Purpose

The module creates a fresh spoken challenge for each verification attempt and verifies three independent signals:

- voice authenticity / deepfake risk
- speaker verification
- challenge phrase matching

If any layer fails or cannot be completed, the result is intentionally conservative and returns `INCONCLUSIVE` or a rejection state rather than silently treating the call as safe.

## Architecture

- `challenge_generator.py`: creates a random challenge phrase
- `challenge_session.py`: tracks expiry, attempts, and challenge state
- `phrase_verifier.py`: normalizes and checks the spoken phrase
- `challenge_service.py`: coordinates generation, validation, and final decision
- `models.py`: final structured authentication result object
- `config.py`: environment-based configuration

## Challenge Generation

Each challenge is generated with a number, color, and word such as:

- `47 blue mango`
- `82 green tiger`
- `16 yellow river`

The generator uses cryptographically suitable randomness from the Python `secrets` module, and every challenge has a unique ID and expiry timestamp.

## Session Lifecycle

The `ChallengeSession` tracks:

- `challenge_id`
- `phrase`
- `created_at`
- `expires_at`
- `attempt_count`
- `max_attempts`
- `state`
- `response_transcript`

States include:

- `CREATED`
- `WAITING_FOR_RESPONSE`
- `PROCESSING`
- `VERIFIED`
- `FAILED`
- `EXPIRED`

## Phrase Verification

`ChallengePhraseVerifier` normalizes the spoken answer with a careful, explicit rule set. It handles:

- capitalization
- punctuation
- whitespace
- number-word variants such as `forty seven`
- minor formatting differences

It does not allow broad fuzzy matching that would accept unrelated phrases.

## Integration with Existing VoiceShield Components

The challenge flow is designed to reuse the existing security stack instead of creating a separate application:

- existing deepfake detection continues to provide voice authenticity evidence
- the existing speaker verifier is used when available
- the existing risk engine remains the place where risk scoring is aggregated

The challenge module is intentionally independent and can be invoked when the existing risk pipeline marks a call as suspicious or when a user explicitly requests additional verification.

## Result States

The final result supports:

- `AUTHENTICATED`
- `REJECTED`
- `SUSPICIOUS`
- `INCONCLUSIVE`

This is intentionally layered and explainable. It is not treated as a simple `REAL`/`FAKE` label.

## Configuration

The module reads from environment variables such as:

- `CHALLENGE_RESPONSE_ENABLED`
- `CHALLENGE_RESPONSE_TTL_MINUTES`
- `CHALLENGE_RESPONSE_MAX_ATTEMPTS`
- `CHALLENGE_RESPONSE_RISK_THRESHOLD`

## Security Limitations

Challenge-response is a layered defense, not a guarantee against a highly capable attacker who could synthesize a fresh phrase. It raises the cost of impersonation and provides a strong additional independent signal.

## Testing

Run the dedicated unit tests with:

```bash
python -m pytest tests/test_challenge_response.py -q
```
