(function () {
    const API_BASE = window.location.origin;
    const state = {
        active: false,
        challengeId: null,
        challengePhrase: "",
        expiresAt: null,
        recorder: null,
        stream: null,
        mediaChunks: [],
        timer: null,
        attemptCount: 0,
        maxAttempts: 3,
    };

    const challengeConfig = {
        enabled: true,
        riskThreshold: 0.4,
    };

    function getChallengeHost() {
        return document.getElementById("challenge-response-host");
    }

    function setChallengeVisibility(show) {
        const host = getChallengeHost();
        if (!host) return;
        host.classList.toggle("hidden", !show);
    }

    function ensureChallengeMarkup() {
        const host = document.getElementById("challenge-response-host");
        if (host) return host;

        const wrapper = document.createElement("div");
        wrapper.id = "challenge-response-host";
        wrapper.className = "challenge-response-host hidden";
        wrapper.innerHTML = `
            <div class="challenge-card glass-card">
                <div class="card-header">
                    <div>
                        <span class="section-number">03</span>
                        <h2>Additional Verification</h2>
                    </div>
                    <span class="card-tag">VOICE AUTH</span>
                </div>

                <div id="challenge-state" class="challenge-state">
                    <div class="challenge-title">Additional Verification Required</div>
                    <p id="challenge-instruction">Start a fresh challenge to verify the caller.</p>
                    <div id="challenge-phrase-box" class="challenge-phrase-box hidden"></div>
                    <div id="challenge-status" class="challenge-status"></div>
                    <div id="challenge-results" class="challenge-results hidden"></div>
                </div>

                <div class="challenge-actions">
                    <button id="challenge-start-button" class="primary-button" type="button">
                        <span>START CHALLENGE</span>
                        <span class="button-arrow">→</span>
                    </button>
                    <button id="challenge-reset-button" class="secondary-button hidden" type="button">RESET</button>
                </div>
            </div>
        `;

        const workspace = document.querySelector(".workspace");
        if (workspace) {
            workspace.appendChild(wrapper);
        }
        return wrapper;
    }

    function attachChallengeEvents() {
        const host = ensureChallengeMarkup();
        if (!host || host.dataset.bound === "true") return;
        host.dataset.bound = "true";

        const startButton = document.getElementById("challenge-start-button");
        const resetButton = document.getElementById("challenge-reset-button");

        startButton?.addEventListener("click", () => {
            startChallengeVerification();
        });

        resetButton?.addEventListener("click", () => {
            resetChallengeSession();
        });
    }

    function updateChallengeInstruction(message) {
        const element = document.getElementById("challenge-instruction");
        if (element) {
            element.textContent = message;
        }
    }

    function updateChallengeStatus(message, type = "info") {
        const element = document.getElementById("challenge-status");
        if (!element) return;
        element.className = `challenge-status ${type}`;
        element.textContent = message;
    }

    function setChallengePhrase(phrase) {
        const box = document.getElementById("challenge-phrase-box");
        if (!box) return;
        box.textContent = phrase;
        box.classList.remove("hidden");
    }

    function showChallengeResults(rows) {
        const container = document.getElementById("challenge-results");
        if (!container) return;
        container.classList.remove("hidden");
        container.innerHTML = rows
            .map((row) => `
                <div class="challenge-row">
                    <span>${row.label}</span>
                    <strong class="${row.passed ? "success" : "fail"}">${row.value}</strong>
                </div>
            `)
            .join("");
    }

    function showChallengeError(message) {
        updateChallengeInstruction("Verification could not be completed.");
        updateChallengeStatus(message, "error");
        state.active = false;
        const resetButton = document.getElementById("challenge-reset-button");
        if (resetButton) resetButton.classList.remove("hidden");
    }

    function resetChallengeSession() {
        state.active = false;
        state.challengeId = null;
        state.challengePhrase = "";
        state.expiresAt = null;
        state.mediaChunks = [];
        state.attemptCount = 0;
        state.maxAttempts = 3;

        if (state.timer) {
            clearInterval(state.timer);
            state.timer = null;
        }

        if (state.recorder && state.recorder.state === "recording") {
            state.recorder.stop();
        }

        if (state.stream) {
            state.stream.getTracks().forEach((track) => track.stop());
            state.stream = null;
        }

        const box = document.getElementById("challenge-phrase-box");
        if (box) box.classList.add("hidden");

        const results = document.getElementById("challenge-results");
        if (results) {
            results.classList.add("hidden");
            results.innerHTML = "";
        }

        updateChallengeInstruction("Start a fresh challenge to verify the caller.");
        updateChallengeStatus("Idle", "info");
        const startButton = document.getElementById("challenge-start-button");
        if (startButton) startButton.disabled = false;
        const resetButton = document.getElementById("challenge-reset-button");
        if (resetButton) resetButton.classList.add("hidden");
    }

    async function startChallengeVerification() {
        if (!challengeConfig.enabled) {
            updateChallengeStatus("Challenge verification is disabled.", "warning");
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/api/challenge-response/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: "browser-session",
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || "Unable to start challenge.");
            }

            const data = await response.json();
            state.active = true;
            state.challengeId = data.challenge_id;
            state.challengePhrase = data.challenge;
            state.expiresAt = data.expires_at;
            state.attemptCount = 0;
            state.maxAttempts = data.max_attempts || 3;

            setChallengePhrase(data.challenge);
            updateChallengeInstruction("Please say the following phrase exactly:");
            updateChallengeStatus("Challenge ready. Listening for the caller response...", "info");

            const resetButton = document.getElementById("challenge-reset-button");
            if (resetButton) resetButton.classList.remove("hidden");

            await beginListeningForChallengeResponse();
        } catch (error) {
            console.error("Challenge start failed:", error);
            showChallengeError(error.message || "The challenge could not be started.");
        }
    }

    async function beginListeningForChallengeResponse() {
        const startButton = document.getElementById("challenge-start-button");
        if (startButton) startButton.disabled = true;

        try {
            state.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });

            state.recorder = new MediaRecorder(state.stream);
            state.mediaChunks = [];

            state.recorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    state.mediaChunks.push(event.data);
                }
            };

            state.recorder.onstop = async () => {
                if (!state.challengeId || state.mediaChunks.length === 0) {
                    updateChallengeStatus("No response audio was captured.", "warning");
                    return;
                }

                const blob = new Blob(state.mediaChunks, { type: "audio/webm" });
                await submitChallengeResponse(blob);
            };

            state.recorder.start();
            updateChallengeStatus("Listening for the spoken response...", "info");

            const timeoutMs = 15000;
            state.timer = window.setTimeout(() => {
                if (state.recorder && state.recorder.state === "recording") {
                    state.recorder.stop();
                }
                updateChallengeStatus("Challenge response timed out.", "warning");
                showChallengeError("Challenge response timed out. Please try again.");
            }, timeoutMs);
        } catch (error) {
            console.error("Challenge microphone failed:", error);
            showChallengeError("Microphone access is required for challenge verification.");
        }
    }

    async function submitChallengeResponse(blob) {
        if (!state.challengeId) {
            showChallengeError("Challenge session is missing.");
            return;
        }

        const formData = new FormData();
        formData.append("challenge_id", state.challengeId);
        formData.append("audio", blob, "challenge_response.webm");

        try {
            updateChallengeStatus("Verifying the challenge response...", "info");
            const response = await fetch(`${API_BASE}/api/challenge-response/verify`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || "Challenge verification failed.");
            }

            const data = await response.json();
            handleChallengeResult(data);
        } catch (error) {
            console.error("Challenge verification request failed:", error);
            showChallengeError(error.message || "Challenge verification could not complete.");
        }
    }

    function handleChallengeResult(result) {
        if (!result) {
            showChallengeError("Challenge verification returned no result.");
            return;
        }

        const rows = [
            {
                label: "Voice Authenticity",
                value: result.voice_authentic === true ? "Authentic" : result.voice_authentic === false ? "Synthetic" : "Inconclusive",
                passed: result.voice_authentic === true,
            },
            {
                label: "Speaker Verification",
                value: result.speaker_verified === true ? "Matched" : result.speaker_verified === false ? "Mismatch" : "Inconclusive",
                passed: result.speaker_verified === true,
            },
            {
                label: "Challenge Response",
                value: result.challenge_passed === true ? "Phrase matched" : result.challenge_passed === false ? "Phrase mismatch" : "Inconclusive",
                passed: result.challenge_passed === true,
            },
        ];

        showChallengeResults(rows);

        const finalStatus = String(result.status || result.final_status || "INCONCLUSIVE").toUpperCase();

        if (finalStatus === "AUTHENTICATED") {
            updateChallengeStatus("Voice authentication passed.", "success");
            updateChallengeInstruction("Safe to proceed.");
        } else if (finalStatus === "REJECTED") {
            updateChallengeStatus("Voice authentication failed.", "error");
            updateChallengeInstruction("Do not proceed with the call.");
        } else if (finalStatus === "SUSPICIOUS") {
            updateChallengeStatus("Additional verification inconclusive.", "warning");
            updateChallengeInstruction("Exercise caution and use an alternate verification method.");
        } else {
            updateChallengeStatus("Verification is inconclusive.", "warning");
            updateChallengeInstruction("Exercise caution and use an alternate verification method.");
        }

        const startButton = document.getElementById("challenge-start-button");
        if (startButton) startButton.disabled = false;
        const resetButton = document.getElementById("challenge-reset-button");
        if (resetButton) resetButton.classList.remove("hidden");

        if (state.timer) {
            clearInterval(state.timer);
            state.timer = null;
        }

        state.active = false;
    }

    function triggerChallengeIfRequired(riskDetails) {
        const score = Number(riskDetails?.risk?.score ?? riskDetails?.score ?? 0);
        const level = String(riskDetails?.risk?.level ?? riskDetails?.level ?? "LOW").toUpperCase();

        if (!challengeConfig.enabled) return;
        if (score < challengeConfig.riskThreshold * 100 && level !== "HIGH") return;

        const host = ensureChallengeMarkup();
        setChallengeVisibility(true);
        host?.scrollIntoView({
            behavior: "smooth",
            block: "nearest"
        });
    }

    window.VoiceShieldChallengeResponse = {
        start: startChallengeVerification,
        reset: resetChallengeSession,
        triggerIfRequired: triggerChallengeIfRequired,
        setConfig: (config) => {
            if (config) {
                challengeConfig.enabled = config.enabled ?? challengeConfig.enabled;
                challengeConfig.riskThreshold = config.riskThreshold ?? challengeConfig.riskThreshold;
            }
        },
    };

    window.attachChallengeEvents = attachChallengeEvents;

    attachChallengeEvents();
    ensureChallengeMarkup();
    setChallengeVisibility(false);
    updateChallengeStatus("Ready", "info");

    window.addEventListener("voiceshield:challenge-required", (event) => {
        const details = event.detail || {};
        triggerChallengeIfRequired(details);
    });

    window.addEventListener("voiceshield:challenge-show", () => {
        const host = ensureChallengeMarkup();
        setChallengeVisibility(true);
        if (host) host.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
})();
