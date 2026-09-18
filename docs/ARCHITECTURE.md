# VoiceShield AI — System Architecture

## 1. Overview

VoiceShield AI is a **real-time, multi-layer voice security system** designed to detect and respond to voice-cloning impersonation attacks.

Instead of depending on a single classifier, the system combines multiple sources of evidence:

```text
Voice Authenticity
        +
Speaker Identity
        +
Conversation Context
        +
Intent
        +
Challenge Response
        ↓
   Risk Assessment
        ↓
 Security Decision
```

The architecture follows a **defense-in-depth** model: failure or uncertainty in one layer does not automatically determine the entire security outcome.

---

# 2. High-Level Architecture

```text
┌──────────────────────────────────────────────┐
│                  USER / CALLER               │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              WEB FRONTEND                    │
│                                              │
│ HTML + CSS + JavaScript                      │
│                                              │
│ • Audio interaction                          │
│ • Live monitoring                            │
│ • Risk visualization                         │
│ • Challenge-response UI                     │
└──────────────────────┬───────────────────────┘
                       │
                       │ HTTP / Application Events
                       ▼
┌──────────────────────────────────────────────┐
│              FASTAPI API LAYER               │
│                 api/                         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│             SECURITY PIPELINE                │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Audio Processor                          │ │
│ └─────────────────────┬────────────────────┘ │
│                       ▼                      │
│ ┌──────────────────────────────────────────┐ │
│ │ Deepfake / Voice Authenticity Detector  │ │
│ └─────────────────────┬────────────────────┘ │
│                       │                      │
│          ┌────────────┼────────────┐         │
│          ▼            ▼            ▼         │
│   Speaker Verifier  Context      Intent      │
│                    Analyzer     Analyzer      │
│          │            │            │          │
│          └────────────┼────────────┘          │
│                       ▼                       │
│                 Risk Engine                  │
│                       │                       │
│                       ▼                       │
│             Security Decision Engine         │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
               ALLOW / WARN / BLOCK
```

---

# 3. Core Components

## 3.1 Audio Processor

**File:**

```text
app/audio_processor.py
```

Responsible for preparing incoming audio for downstream analysis.

The processing pipeline conceptually converts:

```text
Raw Audio
   ↓
Resampling / Formatting
   ↓
Mono Audio
   ↓
16 kHz Representation
   ↓
Model-Ready Audio
```

A common target representation in the system is:

```text
Sample Rate = 16,000 Hz
Channels    = 1
```

This provides a consistent input format for the speech-analysis components.

---

# 4. Deepfake Detector

**File:**

```text
app/detector.py
```

The detector evaluates whether speech exhibits characteristics associated with genuine or synthetic/manipulated audio.

The current implementation uses:

```text
SpeechAntiSpoofingBenchmarks/
Wav2Vec2-Large-AntiDeepfake
```

with the Wav2Vec2 backbone:

```text
facebook/wav2vec2-large-960h-lv60-self
```

The model produces two-class output representing:

```text
Class 0 → Fake
Class 1 → Real
```

Conceptually:

```text
Audio
  ↓
Wav2Vec2
  ↓
Feature Representation
  ↓
Adaptive Average Pooling
  ↓
Linear Classifier
  ↓
Fake / Real probabilities
```

---

# 5. Real-Time Processing

**Files:**

```text
app/realtime_engine.py
```

and related realtime processing components.

The system processes speech incrementally rather than waiting for the complete interaction.

Conceptually:

```text
Continuous Audio
      ↓
Audio Chunk 1 → Analysis
Audio Chunk 2 → Analysis
Audio Chunk 3 → Analysis
       ...
      ↓
Final Interaction Result
```

For a 5-second chunk at 16 kHz:

```text
5 × 16,000 = 80,000 samples
```

This allows the frontend to receive intermediate analysis results.

---

# 6. Speaker Verification

**File:**

```text
app/speaker_verifier.py
```

Speaker verification compares the current speaker against a trusted speaker representation.

The implementation uses the SpeechBrain speaker-recognition model:

```text
speechbrain/spkrec-ecapa-voxceleb
```

Conceptually:

```text
Current Voice
     ↓
Speaker Embedding
     ↓
Compare With Trusted Embedding
     ↓
Similarity
     ↓
Speaker Match / Mismatch Evidence
```

Speaker verification answers a different question from deepfake detection:

```text
Deepfake Detector:
"Does the speech appear synthetic?"

Speaker Verifier:
"Does the voice resemble the trusted speaker?"
```

---

# 7. Context Analysis

**File:**

```text
app/context_analyzer.py
```

The context analyzer examines the conversation for suspicious security-related patterns.

Examples include:

```text
OTP requests
Financial requests
Credential disclosure
Urgency
Threats
Authority impersonation
Security-setting changes
Suspicious instructions
```

The analyzer can work with English/Hindi/Hinglish-style security phrases where implemented.

Multiple detected signals can contribute to the overall context risk.

A noisy-OR style combination is used conceptually:

```text
Context Risk
=
1 − Π(1 − signalᵢ)
```

This prevents multiple independent suspicious signals from simply being ignored because they occur in the same conversation.

---

# 8. Intent Analysis

**File:**

```text
app/intent_analyzer.py
```

Intent analysis identifies potentially sensitive actions requested during the conversation.

Examples include:

```text
Credential disclosure
OTP sharing
Financial transfer
Link interaction
Software installation
Security-setting changes
Personal-information disclosure
Callback / redirection
Physical actions
```

The result provides another evidence source for context/security assessment.

---

# 9. Risk Engine

**File:**

```text
app/risk_engine.py
```

The Risk Engine combines the available security evidence.

The base evidence categories are:

```text
F = Voice authenticity / fake evidence
M = Speaker mismatch
C = Context risk
```

Base weights are:

```text
Voice authenticity → 50%
Speaker mismatch   → 30%
Context             → 20%
```

Because some evidence may be unavailable, VoiceShield dynamically normalizes the available weights.

Let:

```text
A_F = availability of fake evidence
A_S = availability of speaker evidence
A_C = availability of context evidence
```

Then:

```text
D = 0.50A_F + 0.30A_S + 0.20A_C
```

Normalized weights:

```text
W_F = 0.50A_F / D

W_S = 0.30A_S / D

W_C = 0.20A_C / D
```

The base risk is:

```text
R_base = F W_F + M W_S + C W_C
```

The system can additionally account for corroboration between multiple strong signals.

The final score is normalized to:

```text
0–100
```

with the configured risk bands:

```text
< 40       → LOW
40–<70     → MEDIUM
≥ 70       → HIGH
```

---

# 10. Security Decision Engine

**File:**

```text
app/security_decision.py
```

The Security Decision Engine converts security evidence/risk information into an operational action.

The main actions are:

```text
LOW
 ↓
ALLOW

MEDIUM
 ↓
WARN

HIGH
 ↓
BLOCK
```

The decision layer is intentionally separated from the mathematical risk calculation.

Therefore:

```text
Risk Engine
    ↓
"What is the calculated risk?"
    
Decision Engine
    ↓
"What should the system do?"
```

This separation makes the architecture easier to modify and test.

---

# 11. Firewall Orchestration

**File:**

```text
app/firewall.py
```

The firewall acts as the central security coordinator.

It connects components such as:

```text
Audio Processing
Deepfake Detection
Realtime Engine
Speaker Verification
Context Analysis
Intent Analysis
Risk Engine
Security Decision
Transcription
```

Conceptually:

```text
                 Firewall
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Voice         Identity     Context
   Analysis      Analysis     Analysis
       │            │            │
       └────────────┼────────────┘
                    ▼
               Risk Engine
                    │
                    ▼
            Security Decision
```

---

# 12. Challenge-Response Layer

**Directory:**

```text
challenge_response/
```

This is an active verification subsystem.

It provides:

```text
Challenge Generation
Challenge Sessions
Phrase Verification
Adaptive Challenges
Response Consistency
Response Timing
```

The basic flow is:

```text
Generate Challenge
       ↓
User Responds
       ↓
Verify Response
       ↓
Evaluate Consistency
       ↓
Challenge Evidence
```

Adaptive challenges can use conversational claims such as:

```text
Location
Person
Activity
Time
```

The challenge-response result can provide additional evidence to the wider security pipeline.

---

# 13. Transcription Layer

**File:**

```text
app/transcription_service.py
```

Speech transcription converts spoken audio into text that can be consumed by language-oriented components.

Conceptually:

```text
Audio
  ↓
Speech Recognition
  ↓
Transcript
  ↓
Context / Intent Analysis
```

This allows the system to combine:

```text
Acoustic Evidence
+
Linguistic Evidence
```

---

# 14. Complete Data Flow

The complete VoiceShield flow is:

```text
                    AUDIO INPUT
                         │
                         ▼
                  Audio Processor
                         │
                         ▼
                Real-Time Engine
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      Deepfake       Speaker        Transcription
      Detection      Verification       │
          │              │              ▼
          │              │          Context Analysis
          │              │              │
          │              │              ▼
          │              │        Intent Analysis
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                    Risk Engine
                         │
                         ▼
              Security Decision Engine
                         │
                  ┌──────┼──────┐
                  ▼      ▼      ▼
                ALLOW   WARN   BLOCK
```

Challenge-response can be triggered as an additional verification path:

```text
Conversation
     ↓
Challenge
     ↓
Response
     ↓
Verification
     ↓
Additional Evidence
```

---

# 15. Evidence Fusion

VoiceShield does not rely on a single signal.

For example:

```text
Voice appears real
       +
Speaker matches
       +
Conversation requests OTP
```

may produce a different security assessment from:

```text
Voice appears fake
       +
Speaker mismatch
       +
Suspicious financial request
```

The second situation contains multiple corroborating signals.

This is the architectural reason for combining:

```text
Authenticity
Identity
Context
Intent
Challenge evidence
```

rather than using only one classifier.

---

# 16. Frontend Communication

The frontend communicates with the backend through the API/application event layer.

Live analysis is represented through events such as:

```text
chunk_analysis
call_complete
```

The frontend processes these events and updates:

```text
Current chunk
Voice status
Identity status
Context status
Risk
Security decision
```

The backend remains authoritative for security calculations.

---

# 17. Notification Layer

**File:**

```text
notifications/manager.py
```

The notification layer provides application-level notification handling.

Conceptually:

```text
Security Event
      ↓
Notification Manager
      ↓
Frontend Notification
```

The notification mechanism is intended to make important security events visible to the user.

---

# 18. Configuration Layer

**File:**

```text
config/settings.py
```

Centralized configuration prevents security/application parameters from being scattered across unrelated modules.

The architecture therefore separates:

```text
Application Logic
        │
        └── Configuration
```

making environment-specific settings easier to manage.

---

# 19. Architectural Principles

### Defense in Depth

Multiple independent security signals are evaluated.

### Separation of Responsibilities

Each module performs a specific function.

### Evidence-Based Decision Making

The final security state is based on available evidence rather than one hard-coded indicator.

### Dynamic Evidence Availability

Missing evidence is handled rather than automatically treating it as zero risk.

### Real-Time Processing

Audio can be analyzed incrementally.

### Explainability

Security results can be presented as individual evidence components rather than only a final number.

---

# 20. Module Dependency View

```text
                   api/
                    │
                    ▼
                firewall.py
                    │
       ┌────────────┼──────────────┐
       │            │              │
       ▼            ▼              ▼
audio_processor  realtime      transcription
                     │              │
                     ▼              ▼
                 detector      context_analyzer
                     │              │
                     │              ▼
                     │       intent_analyzer
                     │              │
                     └──────┬───────┘
                            │
                            ▼
                       risk_engine
                            │
                            ▼
                    security_decision
                            
speaker_verifier ───────────┘

challenge_response/
        │
        └── Additional active verification path
```

---

# 21. Security Decision Lifecycle

The complete security lifecycle is:

```text
INPUT
  ↓
PROCESS
  ↓
DETECT
  ↓
VERIFY
  ↓
UNDERSTAND CONTEXT
  ↓
ASSESS INTENT
  ↓
FUSE EVIDENCE
  ↓
CALCULATE RISK
  ↓
MAKE DECISION
  ↓
DISPLAY / NOTIFY
```

---

# 22. Example

Suppose a caller claims to be a trusted lecturer.

The system receives:

```text
Voice
 ↓
Audio Processing
 ↓
Deepfake Detection
 ↓
Speaker Verification
 ↓
Transcription
 ↓
Context + Intent Analysis
```

Assume the available evidence indicates:

```text
Voice authenticity → suspicious
Speaker similarity  → low
Conversation        → sensitive request
```

The Risk Engine combines these signals.

The Decision Engine then maps the resulting risk to the configured operational action.

If additional verification is needed:

```text
Challenge
 ↓
Response
 ↓
Verification
```

can provide another evidence source.

---

# 23. Current Architecture Scope

The current architecture is an **application-level AI voice-security pipeline**.

It includes:

* browser frontend;
* FastAPI backend;
* real-time audio processing;
* deepfake voice detection;
* speaker verification;
* speech transcription;
* context analysis;
* intent analysis;
* dynamic risk calculation;
* security decision logic;
* challenge-response verification;
* notification integration.

---

# 24. Features Not Implied by This Architecture

The architecture should not be interpreted as automatically providing:

* blockchain-backed voice identity;
* cryptographic proof of human speech;
* guaranteed prevention of all voice cloning;
* carrier-level telephone blocking;
* immutable long-term evidence storage;
* production-grade telecom integration;
* perfect multilingual understanding.

These require additional implementation and infrastructure.

---

# 25. Summary

VoiceShield AI follows a layered architecture:

```text
┌─────────────────────────────┐
│       User / Frontend       │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│       FastAPI / API         │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│      Audio Processing       │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│ Voice + Identity + Context  │
│        + Intent             │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│       Risk Engine           │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│   Security Decision Engine  │
└──────────────┬──────────────┘
               ▼
        ALLOW / WARN / BLOCK
```

The central architectural idea is:

> **VoiceShield does not ask only whether a voice sounds real. It combines voice authenticity, speaker identity, conversational context, intent, and active verification evidence to produce a security assessment.**
