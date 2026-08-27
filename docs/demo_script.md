# VoiceShield AI — SIH Demo Script

## 1. Introduction

"Voice cloning attacks allow an attacker to imitate a person's voice
using only a small amount of audio.

Our solution is VoiceShield AI, a multi-layer voice security firewall."

## 2. Show the Dashboard

"Instead of relying on a single detector, our system combines three
security signals."

Point to:

- Voice authenticity
- Speaker identity
- Conversation risk

## 3. Safe Call

Select:

REAL / SAFE CALL

Show:

- Voice = REAL
- Speaker = MATCH
- Context = LOW
- Risk = LOW
- Action = ALLOW

Say:

"The voice is classified as authentic, the speaker matches the trusted
reference, and there are no high-risk conversation indicators.
Therefore the firewall allows the call."

## 4. Fake Call

Select:

FAKE / IMPERSONATION CALL

Show:

- Voice = FAKE
- Speaker = MISMATCH
- Context = HIGH
- Risk = HIGH
- Action = BLOCK

Say:

"Here the system detects synthetic audio and the voice does not match
the trusted speaker. Combined with a high-risk conversation context,
the firewall raises the risk score and blocks the call."

## 5. Realtime Detection

Show the chunk results.

Say:

"Instead of waiting for the complete recording, the system divides
audio into smaller chunks and evaluates them independently. This
allows suspicious segments to be detected during an ongoing call."

## 6. Explain the ML

"The deepfake detector uses the official Wav2Vec2-Large AntiDeepfake
checkpoint. We evaluated it on 500 samples from the Release in the Wild
test data and achieved 98.2% accuracy on that evaluation subset."

## 7. Explain Speaker Verification

"The second layer uses ECAPA-TDNN based speaker verification to compare
the caller with a trusted voice reference."

## 8. Explain Risk Engine

"The final decision is not based on one model alone.

The firewall combines:

- voice authenticity,
- speaker identity,
- and conversation risk.

This produces a dynamic security score and action."

## 9. Closing

"Our goal is to transform voice-cloning detection from a standalone
classifier into a practical real-time security firewall."