/* ============================================================
   VOICESHIELD SECURITY NOTIFICATIONS
============================================================ */

(function initializeSecurityNotifications() {

    const API_BASE = "http://127.0.0.1:8000";
    const storageKey = "voiceshield-last-notification-id";
    let lastNotificationId = Number(
        localStorage.getItem(storageKey) || 0
    );
    let permissionRequested = false;
    let notificationAudioContext = null;

    function unlockAlertSound() {

        if (!(window.AudioContext || window.webkitAudioContext)) {
            return;
        }

        if (!notificationAudioContext) {
            notificationAudioContext =
                new (window.AudioContext || window.webkitAudioContext)();
        }

        if (notificationAudioContext.state === "suspended") {
            notificationAudioContext.resume();
        }
    }

    function playAlertSound() {

        try {
            unlockAlertSound();

            const oscillator =
                notificationAudioContext.createOscillator();
            const gain =
                notificationAudioContext.createGain();
            const start = notificationAudioContext.currentTime;

            oscillator.type = "sine";
            oscillator.frequency.setValueAtTime(740, start);
            oscillator.frequency.setValueAtTime(620, start + 0.12);
            gain.gain.setValueAtTime(0.0001, start);
            gain.gain.exponentialRampToValueAtTime(0.12, start + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.28);

            oscillator.connect(gain);
            gain.connect(notificationAudioContext.destination);
            oscillator.start(start);
            oscillator.stop(start + 0.3);
        } catch (error) {
            console.debug("Notification sound unavailable.");
        }
    }

    function showToast(notification) {

        const toast = document.createElement("div");
        toast.className = `security-toast ${notification.severity}`;
        toast.setAttribute("role", "alert");
        toast.innerHTML = `
            <strong>${escapeHtml(notification.title)}</strong>
            <span>${escapeHtml(notification.message)}</span>
        `;

        document.body.appendChild(toast);

        window.setTimeout(() => {
            toast.classList.add("closing");
            window.setTimeout(() => toast.remove(), 250);
        }, 9000);
    }

    function escapeHtml(value) {
        const element = document.createElement("div");
        element.textContent = value;
        return element.innerHTML;
    }

    async function notify(notification) {

        showToast(notification);
        playAlertSound();

        if (
            !permissionRequested &&
            "Notification" in window &&
            Notification.permission === "default"
        ) {
            permissionRequested = true;
            await Notification.requestPermission();
        }

        if (
            "Notification" in window &&
            Notification.permission === "granted"
        ) {
            new Notification(notification.title, {
                body: notification.message,
                tag: `voiceshield-${notification.id}`,
            });
        }

        try {
            await fetch(
                `${API_BASE}/api/notifications/${notification.id}/acknowledge`,
                { method: "POST" }
            );
        } catch (error) {
            console.warn("Notification acknowledgment failed:", error);
        }
    }

    async function poll() {

        try {
            const response = await fetch(
                `${API_BASE}/api/notifications?since_id=${lastNotificationId}`
            );

            if (!response.ok) {
                return;
            }

            const data = await response.json();

            for (const notification of data.notifications || []) {
                lastNotificationId = Math.max(
                    lastNotificationId,
                    Number(notification.id)
                );
                localStorage.setItem(
                    storageKey,
                    String(lastNotificationId)
                );
                await notify(notification);
            }
        } catch (error) {
            console.debug("Security notification service unavailable.");
        }
    }

    poll();
    window.setInterval(poll, 3000);

    document.addEventListener("pointerdown", unlockAlertSound, {
        once: true,
    });

    const testButton =
        document.getElementById("test-notification-button");

    if (testButton) {
        testButton.addEventListener("click", async () => {
            unlockAlertSound();

            try {
                const response = await fetch(
                    `${API_BASE}/api/notifications/test`,
                    { method: "POST" }
                );

                if (!response.ok) {
                    throw new Error(`Test alert failed (${response.status})`);
                }

                await poll();
            } catch (error) {
                console.error("Test notification failed:", error);
            }
        });
    }

})();
