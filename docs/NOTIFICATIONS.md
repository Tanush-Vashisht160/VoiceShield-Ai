# Security Notifications

VoiceShield emits notifications only for serious risk levels:

- `MEDIUM` / `WARN` creates a warning.
- `HIGH` / `HOLD` / `BLOCK` creates a critical alert.

The backend keeps a bounded in-memory alert feed at:

- `GET /api/notifications?since_id=0`
- `POST /api/notifications/{notification_id}/acknowledge`

The frontend polls the feed every three seconds. It displays an in-app toast and uses the browser Notification API for PC and mobile browsers that support notifications. The user must grant notification permission, and the page must remain open. Persistent notifications after the page is closed require a later Web Push service with VAPID credentials and HTTPS.

The feed is process-local and is cleared when the API process restarts. This keeps the feature additive and avoids changing the current analysis storage behavior.
