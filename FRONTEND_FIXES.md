# VoiceShield AI — Frontend Architecture, Fixes & Integration Notes

> **File:** `FRONTEND_FIXES.md`
> **Project:** VoiceShield AI
> **Purpose:** Document the frontend-side fixes, real-time monitoring behavior, event handling, challenge-response integration, and UI synchronization used by VoiceShield AI.

---

## 1. Document Purpose

The VoiceShield AI frontend is responsible for presenting the security analysis performed by the backend in a way that is understandable during a live voice interaction.

The frontend does **not** independently decide whether a voice is genuine or cloned.

Instead, it acts as the presentation and interaction layer between:

```text
User / Caller
     │
     ▼
Browser Frontend
     │
     ├── Audio recording
     ├── Challenge interaction
     ├── Real-time event handling
     ├── Security result rendering
     └── Notification display
     │
     ▼
FastAPI Backend
     │
     ├── Audio processing
     ├── Deepfake detection
     ├── Speaker verification
     ├── Context analysis
     ├── Intent analysis
     ├── Risk calculation
     └── Security decision
```

The frontend therefore has two major responsibilities:

1. **Collect and display interaction data.**
2. **Keep the displayed security state synchronized with backend analysis.**

---

# 2. Why Frontend Fixes Were Required

A real-time security application cannot simply display one final result after an entire call has finished.

For VoiceShield AI, the user needs to see how the security assessment develops during the interaction.

For example:

```text
Incoming voice
      ↓
Audio chunk received
      ↓
Deepfake analysis
      ↓
Speaker analysis
      ↓
Context analysis
      ↓
Risk update
      ↓
Frontend updates
      ↓
Next audio chunk
      ↓
...
      ↓
Final call result
```

This creates a continuously changing security state.

Without proper frontend synchronization, several problems can occur:

* old results may remain visible;
* chunk numbers may not update correctly;
* live results may appear in the wrong order;
* the final result may overwrite intermediate information incorrectly;
* challenge-response events may not reach the appropriate UI;
* security scores may visually disagree with the actual numerical value;
* the interface may appear static even though the backend is processing audio.

The frontend fixes address these synchronization and presentation problems.

---

# 3. Frontend Technology

The current frontend is implemented using standard browser technologies:

| Technology        | Purpose                                        |
| ----------------- | ---------------------------------------------- |
| HTML              | Application structure                          |
| CSS               | Layout, styling and visual security indicators |
| JavaScript        | Application logic and event handling           |
| MediaRecorder API | Browser-side audio recording                   |
| Browser APIs      | Audio and notification interaction             |
| FastAPI API       | Communication with backend services            |

The implementation deliberately keeps the frontend lightweight rather than introducing a large frontend framework.

---

# 4. Frontend Structure

The frontend is organized approximately as follows:

```text
frontend/
│
├── index.html
│
├── css/
│   ├── style.css
│   └── challenge-response.css
│
└── js/
    ├── app.js
    └── challenge-response.js
```

---

# 5. Responsibility of Each Frontend File

## 5.1 `frontend/index.html`

This is the primary HTML document.

It provides the structural layout of the VoiceShield interface.

Conceptually:

```text
HTML Page
│
├── Application Header
│
├── Call / Voice Analysis Interface
│
├── Security Status
│
├── Risk Information
│
├── Live Analysis
│
├── Speaker / Identity Information
│
├── Context / Threat Information
│
├── Challenge-Response Interface
│
└── Notification / Result Areas
```

HTML defines **what exists on the page**.

JavaScript determines **how those elements behave**.

CSS determines **how those elements look**.

---

# 6. Main JavaScript Responsibilities

The main application behavior is handled by:

```text
frontend/js/app.js
```

It is responsible for coordinating frontend interaction with the backend.

Typical responsibilities include:

* starting analysis;
* handling returned analysis information;
* updating live analysis;
* rendering security results;
* maintaining live chunk state;
* processing call completion;
* updating visible risk information;
* connecting frontend components with backend events.

The important design principle is:

> **Backend analysis is authoritative; frontend JavaScript is responsible for rendering that analysis consistently.**

---

# 7. Real-Time Analysis Architecture

VoiceShield processes voice interaction in chunks rather than waiting for the entire recording.

The frontend therefore needs to understand the concept of a **live analysis event**.

The general architecture is:

```text
                VOICE INPUT
                    │
                    ▼
             Browser Recording
                    │
                    ▼
             Backend Processing
                    │
                    ▼
          Real-Time Analysis Event
                    │
                    ▼
        handleLiveAnalysisEvent()
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   chunk_analysis        call_complete
          │                   │
          ▼                   ▼
 renderLiveChunkResult    Final Result
          │
          ▼
     Update UI
```

This event-driven design prevents the frontend from treating the entire call as a single static result.

---

# 8. `handleLiveAnalysisEvent`

A central part of the real-time frontend behavior is the event-handling mechanism represented by:

```javascript
handleLiveAnalysisEvent
```

Its purpose is to receive analysis events and route them to the appropriate frontend behavior.

The important event types include:

```text
chunk_analysis
call_complete
```

---

# 9. `chunk_analysis` Event

A `chunk_analysis` event represents analysis associated with an individual audio chunk.

Conceptually:

```text
Audio Chunk 1
     ↓
Backend Analysis
     ↓
chunk_analysis
     ↓
Frontend
     ↓
Display Chunk 1 Result
```

Then:

```text
Audio Chunk 2
     ↓
Backend Analysis
     ↓
chunk_analysis
     ↓
Frontend
     ↓
Display Chunk 2 Result
```

This continues throughout the interaction.

---

# 10. Why Chunk-Based Rendering Matters

Consider a five-chunk interaction.

Without live rendering:

```text
Chunk 1
Chunk 2
Chunk 3
Chunk 4
Chunk 5
    ↓
Wait
    ↓
Final Result
```

The user receives no intermediate information.

With live rendering:

```text
Chunk 1 → Result displayed
Chunk 2 → Result displayed
Chunk 3 → Result displayed
Chunk 4 → Result displayed
Chunk 5 → Result displayed
             ↓
         Final Result
```

This is much more suitable for a **real-time security system** because the security state can change during the conversation.

---

# 11. Live Chunk Index

The frontend maintains the concept of:

```text
live_chunk_index
```

This identifies the current audio-analysis segment.

A simplified representation is:

```text
Chunk 0
  ↓
Chunk 1
  ↓
Chunk 2
  ↓
Chunk 3
  ↓
...
```

The index is important because the frontend must associate each returned analysis with the correct portion of the interaction.

Without chunk identification, the UI could display:

```text
Analysis A
Analysis C
Analysis B
```

even when the actual processing order was:

```text
A → B → C
```

---

# 12. `renderLiveChunkResult`

After a live analysis event has been received, the frontend uses the rendering layer to update the interface.

The relevant functionality is represented by:

```javascript
renderLiveChunkResult
```

Its conceptual responsibility is:

```text
Backend Chunk Result
        │
        ▼
Extract relevant values
        │
        ▼
Identify current chunk
        │
        ▼
Update corresponding UI elements
        │
        ▼
Display current security state
```

This separates **event processing** from **visual rendering**.

That separation makes the frontend easier to maintain.

---

# 13. Live Monitor State

The frontend also maintains live monitoring state through:

```javascript
window.voiceShieldLiveMonitor
```

The property:

```javascript
window.voiceShieldLiveMonitor.analyzed
```

is used as part of the frontend's live-analysis state.

The purpose of maintaining explicit state is to prevent the interface from behaving as though analysis has not occurred when analysis data has already been received.

Conceptually:

```text
Backend Event
     │
     ▼
Receive analysis
     │
     ▼
Update monitor state
     │
     ▼
Mark analyzed
     │
     ▼
Render current state
```

---

# 14. Call Completion

The frontend distinguishes between an individual chunk result and completion of the complete interaction.

The event:

```text
call_complete
```

represents the completion stage.

The distinction is important:

```text
chunk_analysis
     =
intermediate analysis
```

whereas:

```text
call_complete
     =
complete interaction result
```

Therefore the UI should not treat every chunk as the final security decision.

---

# 15. Complete Live Analysis Flow

The complete frontend sequence can be represented as:

```text
┌──────────────────────┐
│ User speaks          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Browser records audio│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Backend receives     │
│ audio chunk          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Backend performs     │
│ security analysis    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ chunk_analysis event │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────┐
│ handleLiveAnalysisEvent  │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ renderLiveChunkResult    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────┐
│ Update live UI       │
└──────────┬───────────┘
           │
           ▼
     More audio?
       /       \
     YES       NO
      │         │
      ▼         ▼
 Next chunk   call_complete
                  │
                  ▼
           Final UI state
```

---

# 16. Security Information Display

The frontend can present several dimensions of the backend's analysis.

The major conceptual dimensions are:

```text
Voice Authenticity
        │
        ├── Deepfake / synthetic voice analysis
        │
        ▼
Speaker Identity
        │
        ├── Speaker verification
        │
        ▼
Conversation Context
        │
        ├── Suspicious linguistic/security context
        │
        ▼
Intent
        │
        ├── Potentially dangerous requested action
        │
        ▼
Overall Risk
        │
        ▼
Security Decision
```

The frontend's role is to make these results understandable without replacing the backend's calculations.

---

# 17. Risk Visualization

VoiceShield uses numerical security information together with human-readable categories.

A typical conceptual mapping is:

```text
Risk Score
    │
    ├── LOW
    │
    ├── MEDIUM
    │
    └── HIGH
```

The UI should therefore distinguish:

* numerical score;
* risk category;
* underlying evidence;
* security action.

For example:

```text
Risk Score: 82
Risk Level: HIGH
Decision: BLOCK
```

The number and the visual indicator should represent the **same underlying value**.

---

# 18. Percentage-to-Visual Mapping

A common frontend visualization is a circular or progress-based security indicator.

If:

```text
Risk = 70
```

then the visual representation should correspond to:

```text
70%
```

and not accidentally display approximately:

```text
50%
```

because the CSS/JavaScript conversion used a different scale.

The frontend therefore needs a consistent mapping:

```text
Backend score
      ↓
Normalize to UI scale
      ↓
Update progress / circle
      ↓
Update displayed number
```

The displayed numerical value and visual fill should always originate from the same normalized value.

---

# 19. Important Frontend Principle: One Source of Truth

A major rule for security dashboards is:

> **Do not calculate the security result independently in multiple UI components.**

For example, avoid:

```text
Threat Circle → own calculation
Risk Number   → different calculation
Risk Label    → third calculation
```

because this can produce:

```text
Score: 33
Circle: 50%
Level: LOW
```

even though these values should describe the same security state.

Instead:

```text
Backend Risk Result
        │
        ▼
Single normalized frontend value
        │
   ┌────┼────┐
   ▼    ▼    ▼
Number Circle Label
```

This keeps the UI internally consistent.

---

# 20. Challenge-Response Frontend

VoiceShield also includes a challenge-response interface.

The challenge-response frontend logic is separated into:

```text
frontend/js/challenge-response.js
```

and styling is provided through:

```text
frontend/css/challenge-response.css
```

This separation prevents challenge-specific UI logic from becoming unnecessarily coupled with the main application logic.

---

# 21. Challenge-Response Concept

Challenge-response adds an interaction step where the system asks the speaker to respond to a generated challenge.

Conceptually:

```text
System
  │
  ▼
Generate Challenge
  │
  ▼
Display Challenge
  │
  ▼
User Responds
  │
  ▼
Record Response
  │
  ▼
Send Response
  │
  ▼
Verify Response
  │
  ▼
Display Result
```

This is different from simply asking the user to speak freely.

The system controls the requested response.

---

# 22. Why Challenge-Response Exists

A passive detector analyzes whatever speech happens to be available.

Challenge-response introduces an active verification interaction.

For example:

```text
System:
"Please repeat the displayed phrase."

User:
Repeats phrase.

System:
Verifies response.
```

The frontend therefore needs to manage:

1. challenge presentation;
2. recording;
3. response submission;
4. processing state;
5. success/failure state;
6. appropriate UI transitions.

---

# 23. Challenge Frontend State

A challenge interaction naturally has several stages:

```text
CREATED
   ↓
WAITING FOR RESPONSE
   ↓
PROCESSING
   ↓
VERIFIED
```

or:

```text
WAITING
   ↓
PROCESSING
   ↓
FAILED
```

The frontend must display the appropriate state rather than leaving the user uncertain about what is happening.

---

# 24. Challenge Recording

The browser uses audio-recording capabilities to capture the response.

The general process is:

```text
User presses response/start control
             ↓
Browser requests microphone access
             ↓
Recording begins
             ↓
User speaks
             ↓
Recording stops
             ↓
Audio response prepared
             ↓
Backend verification
```

The browser's recording APIs provide the mechanism for capturing the response; the backend remains responsible for security analysis and verification.

---

# 25. Challenge UI Separation

Challenge-response styling is separated into:

```text
challenge-response.css
```

while challenge-specific JavaScript behavior is contained in:

```text
challenge-response.js
```

This provides a cleaner architecture:

```text
Main Application
       │
       ├── app.js
       │
       └── Challenge Module
               │
               ├── challenge-response.js
               └── challenge-response.css
```

---

# 26. Challenge Event Integration

The challenge system can be attached to the main VoiceShield frontend through the challenge event integration.

The frontend architecture uses integration points such as:

```javascript
window.attachChallengeEvents
```

and:

```javascript
window.VoiceShieldChallengeResponse
```

These expose challenge-response functionality to the main application without requiring all challenge implementation details to exist inside `app.js`.

---

# 27. Frontend Event-Driven Design

VoiceShield's frontend can therefore be viewed as an event-driven system.

```text
                   Browser
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
   Audio Event   Challenge Event  UI Event
       │              │              │
       └──────────────┼──────────────┘
                      ▼
              Application Logic
                      │
                      ▼
                 UI Update
```

This architecture is preferable to continuously polling every UI element independently.

---

# 28. CSS Architecture

The styling is divided into:

```text
frontend/css/style.css
```

for the main application and:

```text
frontend/css/challenge-response.css
```

for challenge-specific components.

This provides separation between:

```text
Core Dashboard Styling
```

and:

```text
Challenge Interaction Styling
```

---

# 29. Visual Security Indicators

Security applications require clear visual hierarchy.

The frontend should distinguish between:

### Informational state

```text
Analysis in progress
```

### Low-risk state

```text
LOW
```

### Medium-risk state

```text
MEDIUM
```

### High-risk state

```text
HIGH
```

### Processing state

```text
ANALYZING
```

The visual presentation should make the current system state immediately understandable.

---

# 30. Example Real-World Interaction

Consider a lecturer receiving a suspicious call.

### Step 1 — Voice begins

The browser starts collecting audio.

```text
Caller speaks
     ↓
Audio chunk
```

### Step 2 — Backend analyzes the chunk

The backend performs its available security checks.

```text
Voice authenticity
Speaker identity
Context
Intent
```

### Step 3 — Frontend receives result

The frontend receives:

```text
chunk_analysis
```

### Step 4 — UI updates

The live monitor displays the latest information.

```text
Current Chunk
Risk
Voice Status
Identity Status
Context Status
```

### Step 5 — More speech

The process repeats.

```text
Chunk 1
Chunk 2
Chunk 3
Chunk 4
...
```

### Step 6 — Interaction ends

The backend emits:

```text
call_complete
```

The frontend transitions to the completed interaction state.

---

# 31. Example of Why Live Updates Matter

Suppose an interaction initially looks normal:

```text
Chunk 1
Voice: Real
Context: Normal
Risk: Low
```

Later, the caller starts requesting sensitive information:

```text
Chunk 4
Voice: Suspicious
Context: Financial / Security-related
Risk: Higher
```

The frontend must reflect the latest available evidence.

This is why VoiceShield's interface is designed around **incremental analysis rather than one static result**.

---

# 32. Frontend and Backend Separation

A key architectural principle is:

```text
FRONTEND
Presentation + interaction
        │
        │ API / Events
        ▼
BACKEND
Security analysis + decision
```

The frontend should not be considered the security engine.

For example:

```text
Frontend:
"Display risk = 82"
```

rather than:

```text
Frontend:
"Determine whether this person is a cloned voice."
```

The latter belongs to the backend security pipeline.

---

# 33. Error-State Handling

A real-world security interface must also distinguish:

```text
LOW RISK
```

from:

```text
NO DATA
```

and:

```text
ANALYSIS ERROR
```

These are not equivalent.

For example:

```text
Risk = 0
```

does not necessarily mean:

```text
The caller is definitely safe.
```

It can instead indicate that a particular evidence source was unavailable or that no suspicious signal was detected.

The frontend therefore needs to preserve the meaning of backend status fields rather than blindly converting missing information into a security score.

---

# 34. Handling `N/A` States

Some security evidence may legitimately be unavailable.

For example:

```text
Speaker Identity: N/A
```

means that speaker identity information is not currently available.

It should not automatically become:

```text
Speaker Match: 0%
```

because these represent different meanings.

A professional security UI should distinguish:

```text
N/A
```

from:

```text
0
```

and:

```text
FAILED
```

---

# 35. Data Flow Summary

The frontend data flow can be summarized as:

```text
                   USER
                    │
                    ▼
             Browser Interface
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
     Voice Input       Challenge Input
          │                   │
          ▼                   ▼
       Backend API / Events
          │                   │
          └─────────┬─────────┘
                    ▼
             Security Results
                    │
                    ▼
          handleLiveAnalysisEvent
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
   chunk_analysis         call_complete
          │                    │
          ▼                    ▼
renderLiveChunkResult     Final State
          │
          ▼
       Live UI
```

---

# 36. Frontend Fix Categories

The frontend fixes can broadly be classified into the following categories.

## 36.1 Event Synchronization

Ensuring that backend events are correctly handled by the browser.

```text
Backend event
      ↓
Correct handler
      ↓
Correct UI state
```

---

## 36.2 Live Chunk Rendering

Ensuring individual analysis chunks appear as they are processed.

```text
Chunk N
  ↓
Result
  ↓
UI
```

---

## 36.3 State Synchronization

Maintaining explicit state so that different frontend components do not contradict each other.

---

## 36.4 Challenge Integration

Keeping challenge-response behavior modular while allowing it to communicate with the main application.

---

## 36.5 Visual Consistency

Ensuring:

```text
Numerical score
      =
visual representation
      =
risk category
```

when they represent the same underlying metric.

---

## 36.6 Missing-Data Handling

Preventing unavailable evidence from being incorrectly displayed as a valid zero-valued result.

---

# 37. Security Design Considerations

The frontend is part of the security product, but it should not be treated as a trusted security boundary.

A browser-based interface can be manipulated by the user.

Therefore:

> **Security decisions must be enforced by backend logic rather than relying solely on frontend controls.**

For example, hiding a button in JavaScript is not equivalent to enforcing authorization on the server.

The frontend is primarily responsible for:

* interaction;
* visualization;
* status presentation;
* user feedback.

The backend is responsible for:

* analysis;
* evidence fusion;
* risk calculation;
* security decisions.

---

# 38. Performance Considerations

Real-time interfaces must avoid unnecessary work.

The frontend therefore benefits from:

* event-driven updates;
* updating only relevant UI elements;
* separating challenge logic from the main application;
* maintaining explicit live-analysis state;
* avoiding unnecessary repeated DOM operations.

The objective is:

```text
New backend event
      ↓
Minimal required UI update
```

rather than:

```text
New backend event
      ↓
Rebuild entire application
```

---

# 39. Maintainability

The current frontend organization provides logical separation:

```text
index.html
    │
    ├── Structure
    │
    ▼
style.css
    │
    ├── Main visual design
    │
    ▼
app.js
    │
    ├── Application behavior
    │
    ▼
challenge-response.js
    │
    └── Challenge behavior
```

This makes it easier to modify one subsystem without unnecessarily changing unrelated components.

---

# 40. Testing the Frontend Integration

Frontend correctness should be evaluated together with the backend event contract.

Important scenarios include:

### Scenario A — Normal analysis

```text
Audio
 ↓
chunk_analysis
 ↓
UI update
```

### Scenario B — Multiple chunks

```text
Chunk 1
Chunk 2
Chunk 3
...
 ↓
Correct ordering
```

### Scenario C — Call completion

```text
chunk_analysis
 ↓
call_complete
 ↓
Final state
```

### Scenario D — Challenge

```text
Challenge
 ↓
Response
 ↓
Processing
 ↓
Verification
 ↓
UI result
```

### Scenario E — Missing evidence

```text
Speaker = N/A
```

The frontend should preserve the unavailable state rather than inventing a numerical match.

---

# 41. Known Frontend-Level Validation Principle

During development, particular attention should be paid to mismatches between:

```text
Displayed Score
```

and:

```text
Graphical Indicator
```

For example, if the application reports:

```text
Risk = 33
```

the corresponding visual progress should be derived from the same value.

A frontend bug can therefore be present even when the backend calculation is correct.

This distinction is important when debugging VoiceShield:

```text
Backend calculation bug
        ≠
Frontend rendering bug
```

---

# 42. What This Frontend Layer Actually Implements

The frontend currently provides the application-facing layer for:

* browser-based voice interaction;
* audio recording interaction;
* live analysis event handling;
* chunk-based result rendering;
* live monitor state;
* call-completion handling;
* security result visualization;
* challenge-response interaction;
* challenge-specific UI;
* browser notification-related presentation where integrated with the application.

The frontend communicates the backend's analysis rather than replacing the underlying security algorithms.

---

# 43. What Is Not Claimed as a Frontend Feature

The following should **not** be described as frontend capabilities unless corresponding implementation is added and verified:

* cryptographic voice identity;
* blockchain-backed identity;
* immutable evidence storage;
* guaranteed prevention of voice cloning;
* cryptographic proof that a speaker is human;
* production-grade Web Push infrastructure;
* operating-system-level call blocking;
* carrier-level telephone network integration;
* tamper-proof frontend security.

These require additional infrastructure beyond the browser UI.

---

# 44. Recommended Mental Model

The easiest way to understand the VoiceShield frontend is:

```text
             VOICE SHIELD UI
                   │
       ┌───────────┴───────────┐
       │                       │
   INTERACTION             MONITORING
       │                       │
       ├── Recording            ├── Live chunks
       ├── Challenge            ├── Risk
       └── User controls        ├── Identity
                                ├── Context
                                └── Decision
                                       │
                                       ▼
                                BACKEND ENGINE
```

The frontend is therefore the **real-time security dashboard and interaction layer**.

---

# 45. Final Architecture

The complete application-facing architecture can be represented as:

```text
┌─────────────────────────────────────────────┐
│                USER / CALLER                │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│             BROWSER FRONTEND                │
│                                             │
│  HTML                                        │
│  CSS                                         │
│  JavaScript                                  │
│                                             │
│  ├── Audio interaction                       │
│  ├── Live monitoring                         │
│  ├── Challenge-response                      │
│  ├── Result visualization                    │
│  └── Notifications                           │
└──────────────────────┬──────────────────────┘
                       │
                       │ API / Events
                       ▼
┌─────────────────────────────────────────────┐
│               FASTAPI BACKEND               │
│                                             │
│  ├── Audio Processing                        │
│  ├── Deepfake Detection                      │
│  ├── Speaker Verification                    │
│  ├── Context Analysis                        │
│  ├── Intent Analysis                         │
│  ├── Risk Engine                             │
│  └── Security Decision                       │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│             SECURITY RESULT                 │
│                                             │
│  Authenticity + Identity + Context + Intent │
│                     ↓                       │
│                Risk / Decision               │
└─────────────────────────────────────────────┘
```

---

# 46. Conclusion

The VoiceShield AI frontend is designed as a **real-time security monitoring and interaction layer** rather than as an independent detection engine.

The major frontend engineering principles are:

1. **Event-driven real-time updates**
2. **Chunk-based analysis rendering**
3. **Explicit live-monitor state**
4. **Clear separation between intermediate and final results**
5. **Modular challenge-response integration**
6. **Consistent score and visualization mapping**
7. **Correct handling of unavailable evidence**
8. **Separation of presentation from backend security decisions**
9. **Clear security-state visualization**
10. **Maintainable separation of HTML, CSS and JavaScript responsibilities**

The result is a frontend capable of presenting VoiceShield's multi-layer voice-security pipeline as a continuous security-monitoring experience rather than a simple upload-and-result interface.

---

## File References

```text
frontend/
├── index.html
├── css/
│   ├── style.css
│   └── challenge-response.css
└── js/
    ├── app.js
    └── challenge-response.js
```

**Primary real-time integration concepts:**

```text
handleLiveAnalysisEvent()
        │
        ├── chunk_analysis
        │       ↓
        │   renderLiveChunkResult()
        │
        └── call_complete
                ↓
           Final UI State

window.voiceShieldLiveMonitor
        │
        └── analyzed

Challenge Integration
        │
        ├── window.attachChallengeEvents
        └── window.VoiceShieldChallengeResponse
```

> **Documentation principle:** This document describes the frontend architecture and implemented integration concepts. Backend security algorithms, model internals, risk-engine mathematics, and challenge verification logic should be documented in their respective technical documents rather than duplicated here.
