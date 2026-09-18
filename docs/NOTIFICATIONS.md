# VoiceShield AI — Notification System

## 1. Overview

VoiceShield AI includes a lightweight notification layer for communicating important security events from the backend to the frontend.

The notification system is designed to inform the user when an event such as a suspicious call, high-risk detection, blocked interaction, or verification result requires attention.

The current implementation is **process-local and in-memory**. It is intended for the VoiceShield prototype/demo environment and does not depend on an external notification service.

---

## 2. Purpose

The notification layer provides a bridge between:

```text
Security Analysis
      ↓
Firewall / Decision Engine
      ↓
Notification Manager
      ↓
REST API
      ↓
Frontend
      ↓
User Notification
```

Instead of requiring the frontend to continuously inspect every internal security component, the backend can create a notification whenever an important event occurs.

### Main objectives

* Report important security events.
* Keep notifications available to the frontend.
* Support acknowledgement of notifications.
* Provide a simple REST interface.
* Display browser-level notifications where supported.
* Keep the implementation lightweight for local deployment and demonstrations.

---

# 3. Implementation

The main notification implementation is located at:

```text
notifications/
└── manager.py
```

The frontend consumes notification data through the backend API.

The notification system is therefore separate from the core detection models.

```text
app/
├── detector.py
├── speaker_verifier.py
├── context_analyzer.py
├── intent_analyzer.py
├── risk_engine.py
└── security_decision.py

        ↓

notifications/
└── manager.py

        ↓

api/server.py

        ↓

frontend/
```

This separation keeps security analysis and user-interface notification handling independent.

---

# 4. Notification Lifecycle

A notification follows this general lifecycle:

```text
1. Security event occurs
          ↓
2. Backend creates notification
          ↓
3. Notification stored in notification manager
          ↓
4. Frontend requests notifications
          ↓
5. Notification displayed to user
          ↓
6. User acknowledges notification
          ↓
7. Backend marks notification acknowledged
```

This allows the security pipeline to generate events without directly controlling frontend UI components.

---

# 5. Notification Data

A notification represents an event that should be communicated to the user.

Conceptually, a notification contains information such as:

```text
Notification
├── ID
├── Type / event category
├── Message
├── Severity
├── Timestamp
└── Acknowledgement state
```

The exact fields should be treated according to the current implementation in `notifications/manager.py`.

The important distinction is that a notification is **not itself the risk score**.

For example:

```text
Risk Engine
    ↓
Risk Score = 82
    ↓
Security Decision = BLOCK
    ↓
Notification
    ↓
"High-risk voice interaction blocked"
```

The risk engine performs the security analysis, while the notification layer communicates the resulting event.

---

# 6. Notification API

The current backend exposes notification endpoints for frontend integration.

## 6.1 Get Notifications

```http
GET /api/notifications?since_id=0
```

This endpoint allows the frontend to retrieve notifications.

The `since_id` parameter allows the frontend to request notifications newer than a previously processed notification ID.

### Example

```text
Frontend
   │
   │ GET /api/notifications?since_id=10
   ↓
FastAPI
   │
   ↓
Notification Manager
   │
   ↓
Notifications newer than ID 10
```

This approach avoids requiring the frontend to repeatedly download the complete notification history.

---

# 7. Acknowledge Notification

The backend also provides:

```http
POST /api/notifications/{notification_id}/acknowledge
```

This endpoint is used when the frontend/user acknowledges a notification.

Example:

```text
Notification ID: 15
Status: Unacknowledged
        ↓
User opens notification
        ↓
POST /api/notifications/15/acknowledge
        ↓
Status: Acknowledged
```

Acknowledgement is useful because a security notification can represent an event that has already been displayed but still needs to be tracked by the interface.

---

# 8. Frontend Integration

The frontend periodically communicates with the backend notification API.

The conceptual flow is:

```text
┌──────────────────────────────┐
│       VoiceShield Backend    │
│                              │
│ Security Decision            │
│          ↓                   │
│ Notification Manager         │
└──────────────┬───────────────┘
               │
               │ REST API
               ↓
┌──────────────────────────────┐
│          Frontend            │
│                              │
│ Notification Fetch           │
│          ↓                   │
│ Notification Display         │
│          ↓                   │
│ User Acknowledgement         │
└──────────────────────────────┘
```

The frontend therefore does not need direct access to:

* the deepfake model,
* speaker embeddings,
* context-analysis internals,
* risk-engine calculations, or
* security-decision logic.

It only receives the information necessary to present the event.

---

# 9. Browser Notifications

Where supported by the browser, VoiceShield can use the browser's Notification API to provide an additional user-visible notification.

Conceptually:

```text
Backend Event
      ↓
Frontend receives notification
      ↓
Browser Notification API
      ↓
Desktop / Browser notification
```

This provides a more immediate indication of important security events.

However, browser notification support depends on:

* browser capabilities,
* notification permissions,
* the application's execution environment, and
* user settings.

Therefore, browser notifications should be treated as a UI capability rather than a guaranteed security mechanism.

---

# 10. Relationship With the Security Pipeline

Notifications are downstream from the security analysis pipeline.

A simplified VoiceShield flow is:

```text
Audio
  ↓
Audio Processing
  ↓
Real-Time Chunking
  ↓
Voice Authenticity Detection
  ↓
Speaker Verification
  ↓
Transcription
  ↓
Context Analysis
  ↓
Intent Analysis
  ↓
Risk Engine
  ↓
Security Decision Engine
  ↓
Notification
  ↓
Frontend
```

For example:

### Normal interaction

```text
Authentic voice
      +
Trusted speaker
      +
Low-risk context
      ↓
Low overall risk
      ↓
ALLOW
```

A notification may not be required for every normal event.

### Suspicious interaction

```text
Potentially synthetic voice
        +
Speaker mismatch
        +
OTP request
        +
Urgency
        ↓
High risk
        ↓
BLOCK
        ↓
Security notification
```

The notification communicates the outcome without replacing the underlying analysis.

---

# 11. Example Security Events

Possible notification scenarios include:

| Event                  | Possible User Message                        |
| ---------------------- | -------------------------------------------- |
| Suspicious voice       | Suspicious voice activity detected           |
| Speaker mismatch       | Speaker identity could not be verified       |
| High context risk      | Suspicious conversation context detected     |
| High-risk interaction  | High-risk voice interaction detected         |
| Blocked interaction    | Voice interaction blocked by security policy |
| Challenge required     | Additional verification required             |
| Challenge failed       | Voice verification challenge failed          |
| Verification completed | Additional verification completed            |

The exact notification text should follow the messages generated by the current implementation.

---

# 12. Notification vs Risk Score

These two concepts serve different purposes.

### Risk score

The Risk Engine answers:

> **How risky is the current interaction based on the available evidence?**

For example:

```text
Risk Score: 82
Risk Level: HIGH
```

### Security decision

The Security Decision Engine answers:

> **What should the system do with the interaction?**

For example:

```text
Decision: BLOCK
```

### Notification

The notification system answers:

> **What should the user/interface be told about the security event?**

For example:

```text
High-risk interaction blocked.
```

Therefore:

```text
Evidence
   ↓
Risk Score
   ↓
Security Decision
   ↓
Notification
```

---

# 13. Why Notifications Are Separate

Keeping notifications separate from detection provides several architectural benefits.

### 13.1 Separation of concerns

The detector does not need to know how the frontend displays alerts.

```text
Detector
    ↓
Evidence

Risk Engine
    ↓
Risk

Decision Engine
    ↓
Action

Notification Manager
    ↓
Communication
```

Each component has a focused responsibility.

### 13.2 Easier frontend changes

The notification UI can be modified without changing the deepfake detector.

### 13.3 Easier backend testing

Security components can be tested independently from browser notification behaviour.

### 13.4 Future extensibility

The notification layer can later become an integration point for additional notification mechanisms.

---

# 14. In-Memory Storage

The current notification implementation uses an in-memory feed.

This means notifications are stored inside the running backend process.

Conceptually:

```text
FastAPI Process
      │
      ├── Notification 1
      ├── Notification 2
      ├── Notification 3
      └── Notification 4
```

This is appropriate for a local prototype because it avoids requiring:

* PostgreSQL
* Redis
* MongoDB
* Firebase
* a separate notification server

The notification feed is therefore simple to start and easy to demonstrate.

---

# 15. Process-Local Behaviour

Because notifications are maintained in memory, they belong to the current running application process.

Therefore:

```text
Application running
        ↓
Notifications available
```

but after:

```text
Application restart
        ↓
Previous in-memory notifications are cleared
```

This is an important implementation limitation.

It means the current notification system should **not** be described as a persistent notification history.

---

# 16. Bounded Notification Feed

The notification feed is bounded rather than being an unlimited permanent event database.

This prevents the running process from accumulating an uncontrolled number of notification objects during long demonstrations or development sessions.

Conceptually:

```text
New notification
      ↓
Add to feed
      ↓
Feed reaches configured limit
      ↓
Older entries can be discarded
```

The exact retention limit should be taken from the current `notifications/manager.py` configuration rather than assumed by external documentation.

---

# 17. Example End-to-End Scenario

Consider a suspicious voice interaction:

```text
Caller:
"Your account has been locked.
Press 1 and share the OTP."
```

VoiceShield processes the interaction through multiple evidence sources.

```text
Audio
 ↓
Deepfake Detection
 ↓
Speaker Verification
 ↓
Speech Transcription
 ↓
Context Analysis
 ↓
Intent Analysis
 ↓
Risk Engine
 ↓
Security Decision
```

Suppose the resulting security decision is:

```text
Risk Level: HIGH
Decision: BLOCK
```

The notification layer can then communicate the event:

```text
High-risk interaction blocked.
```

The frontend displays the event to the user.

The important architectural point is:

> The notification did not determine that the call was malicious. It communicated the decision produced by the security pipeline.

---

# 18. Notification Polling Model

The current API design supports a simple polling-based frontend integration.

Conceptually:

```text
Frontend
   │
   │ Request new notifications
   ↓
Backend
   │
   │ Return notifications
   ↓
Frontend
   │
   ├── Display
   └── Acknowledge
```

Using `since_id` allows the frontend to request only newer notifications.

Example:

```text
First request:
GET /api/notifications?since_id=0

Backend:
Notifications 1–5

Frontend stores:
last_seen_id = 5

Next request:
GET /api/notifications?since_id=5

Backend:
Notifications 6–8
```

This is simpler than repeatedly retrieving the entire feed.

---

# 19. Security Considerations

Notifications are an **observability and user-interface layer**, not the primary security enforcement mechanism.

The actual security decision should remain in the backend security pipeline.

For example:

```text
Frontend notification
        X
        ↓
Does NOT independently block audio

Backend Security Decision
        ↓
Determines ALLOW / WARN / BLOCK
```

This is important because frontend code can be modified or bypassed by a client.

Security-critical decisions therefore belong on the backend.

---

# 20. Current Scope

The current notification implementation provides:

* Backend notification management.
* In-memory notification storage.
* Notification retrieval through REST.
* Incremental retrieval using `since_id`.
* Notification acknowledgement.
* Frontend integration.
* Browser Notification API support where available.

---

# 21. Current Limitations

The current implementation does **not** represent a complete production notification infrastructure.

In particular, the prototype does not imply:

* persistent notification history across restarts,
* distributed notification storage,
* guaranteed delivery,
* mobile push notification infrastructure,
* SMS delivery,
* email delivery,
* Firebase Cloud Messaging integration,
* Web Push service infrastructure,
* multi-server notification synchronization.

These would require additional infrastructure.

---

# 22. Possible Production Extension

A production deployment could evolve the notification layer as follows:

```text
                 ┌───────────────┐
                 │ Security Event│
                 └───────┬───────┘
                         ↓
                Notification Service
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Web Push        Email           SMS
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                       User
```

Persistent storage could also be introduced:

```text
Security Event
      ↓
Notification Service
      ↓
Database / Queue
      ↓
Delivery Layer
      ↓
User
```

These are **future architectural extensions**, not claims about the current prototype.

---

# 23. Testing Considerations

The notification layer should be tested independently from the ML models.

Important test cases include:

### Notification creation

```text
Security event
      ↓
Notification created
```

### Notification retrieval

```text
GET /api/notifications
      ↓
Expected notification returned
```

### Incremental retrieval

```text
since_id = N
      ↓
Only newer notifications returned
```

### Acknowledgement

```text
POST /api/notifications/{id}/acknowledge
      ↓
Notification marked acknowledged
```

### Empty feed

```text
No new notifications
      ↓
Empty result
```

### Restart behaviour

```text
Application restart
      ↓
In-memory notifications no longer available
```

---

# 24. Design Principle

The notification system follows a simple principle:

> **Detection produces evidence, decision logic produces an action, and notifications communicate the resulting security event.**

This keeps the architecture understandable:

```text
Detection
   ↓
Evidence

Evidence Fusion
   ↓
Risk

Risk
   ↓
Decision

Decision
   ↓
Notification

Notification
   ↓
User
```

---

# 25. Summary

VoiceShield's notification layer provides the communication path between backend security decisions and the user-facing interface.

Its current implementation is intentionally lightweight:

```text
Security Components
       ↓
Notification Manager
       ↓
REST API
       ↓
Frontend
       ↓
User
```

The system supports notification retrieval, incremental updates, acknowledgement, and browser-level notifications where supported.

The notification layer does **not** replace the deepfake detector, speaker verifier, context analyzer, intent analyzer, Risk Engine, or Security Decision Engine.

Instead, it sits at the final communication stage of the security pipeline, allowing VoiceShield to present important security events clearly while keeping security-critical analysis and enforcement inside the backend.
