(function () {
    const API_BASE = window.location.origin;
    let challengeTranscript = "";
    let speechRecognition = null;

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

    function startChallengeSpeechRecognition() {
        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.warn(
                "Speech Recognition API is not supported."
            );
            speechRecognition = null;
            return;
        }

        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = true;
        speechRecognition.interimResults = true;
        speechRecognition.lang = "en-US";

        challengeTranscript = "";

        speechRecognition.onresult = (event) => {
            let transcript = "";

            for (
                let i = event.resultIndex;
                i < event.results.length;
                i++
            ) {
                transcript +=
                    event.results[i][0].transcript + " ";
            }

            challengeTranscript = transcript.trim();

            console.log(
                "CHALLENGE TRANSCRIPT:",
                challengeTranscript
            );
        };

        speechRecognition.onerror = (event) => {
            console.warn(
                "Challenge speech recognition error:",
                event.error
            );
        };

        speechRecognition.start();
    }

    function stopChallengeSpeechRecognition() {
        if (!speechRecognition) {
            return;
        }

        try {
            speechRecognition.stop();
        } catch (error) {
            console.warn(
                "Speech recognition stop error:",
                error
            );
        }
    }

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

        if (!host) {
            console.error("❌ Challenge markup could not be created");
            return;
        }

        if (host.dataset.bound === "true") {
            return;
        }

        host.dataset.bound = "true";

        const startButton =
            document.getElementById("challenge-start-button");

        const resetButton =
            document.getElementById("challenge-reset-button");

        startButton?.addEventListener("click", () => {
            startChallengeVerification();
        });

        resetButton?.addEventListener("click", () => {
            resetChallengeSession();
        });
    }

        window.attachChallengeEvents = attachChallengeEvents;
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
        stopChallengeSpeechRecognition();
        state.active = false;
        state.challengeId = null;
        state.challengePhrase = "";
        state.expiresAt = null;
        state.mediaChunks = [];
        state.attemptCount = 0;
        state.maxAttempts = 3;

        if (state.timer) {
            clearTimeout(state.timer);
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

            updateChallengeStatus(
                "Challenge verification is disabled.",
                "warning"
            );

            return;

        }

        /*
        * Prevent starting multiple challenges
        */
        if (state.active) {

            console.warn(
                "⚠️ Challenge is already active"
            );

            return;

        }

        try {

            console.log(
                "🚀 Starting challenge session..."
            );

            updateChallengeStatus(
                "Generating a verification challenge...",
                "info"
            );

            const response =
                await fetch(
                    `${API_BASE}/api/challenge-response/start`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type": "application/json"
                        },

                        body: JSON.stringify({
                            session_id: "browser-session"
                        })
                    }
                );

            console.log(
                "📡 Challenge start response:",
                response.status
            );

            if (!response.ok) {

                const errorText =
                    await response.text();

                throw new Error(
                    errorText ||
                    "Unable to start challenge."
                );

            }

            const data =
                await response.json();

            console.log(
                "✅ Challenge received from backend:",
                data
            );

            /*
            * Store challenge information
            */
            state.active = true;

            state.challengeId =
                data.challenge_id;

            state.challengePhrase =
                data.challenge;

            state.expiresAt =
                data.expires_at;

            state.attemptCount = 0;

            state.maxAttempts =
                data.max_attempts || 3;

            /*
            * Show phrase
            */
            setChallengePhrase(
                data.challenge
            );

            updateChallengeInstruction(
                "Please say the following phrase clearly:"
            );

            updateChallengeStatus(
                "Challenge ready. Starting microphone...",
                "info"
            );

            const resetButton =
                document.getElementById(
                    "challenge-reset-button"
                );

            if (resetButton) {

                resetButton.classList.remove(
                    "hidden"
                );

            }

            /*
            * Start microphone and recording
            */
            await beginListeningForChallengeResponse();

        } catch (error) {

            console.error(
                "❌ Challenge start failed:",
                error
            );

            state.active = false;

            showChallengeError(
                error.message ||
                "The challenge could not be started."
            );

        }

    }

    async function beginListeningForChallengeResponse() {

        const startButton =
            document.getElementById("challenge-start-button");

        if (startButton) {
            startButton.disabled = true;
        }

        /*
        * Clear any old transcript before starting
        */
        challengeTranscript = "";

        try {

            console.log("🎤 Requesting microphone for challenge...");

            state.stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: {
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

            console.log("✅ Challenge microphone access granted");

            state.recorder =
                new MediaRecorder(state.stream);

            state.mediaChunks = [];

            /*
            * Collect recorded audio chunks
            */
            state.recorder.ondataavailable = (event) => {

                if (
                    event.data &&
                    event.data.size > 0
                ) {

                    state.mediaChunks.push(event.data);

                }

            };

            /*
            * When recording stops, send audio to backend
            */
            state.recorder.onstop = async () => {

                console.log(
                    "🛑 Challenge recording stopped"
                );

                /*
                * Clear recording timer
                */
                if (state.timer) {

                    clearTimeout(state.timer);

                    state.timer = null;

                }

                /*
                * Stop microphone tracks
                */
                if (state.stream) {

                    state.stream
                        .getTracks()
                        .forEach((track) => track.stop());

                    state.stream = null;

                }

                /*
                * Check audio was captured
                */
                if (
                    !state.challengeId ||
                    state.mediaChunks.length === 0
                ) {

                    console.warn(
                        "⚠️ No challenge audio captured"
                    );

                    updateChallengeStatus(
                        "No response audio was captured. Please try again.",
                        "warning"
                    );

                    if (startButton) {
                        startButton.disabled = false;
                    }

                    return;

                }

                const blob =
                    new Blob(
                        state.mediaChunks,
                        {
                            type:
                                state.mediaChunks[0]?.type ||
                                "audio/webm"
                        }
                    );

                console.log(
                    "📤 Challenge audio captured:",
                    blob.size,
                    "bytes"
                );

                updateChallengeStatus(
                    "Verifying your spoken response...",
                    "info"
                );

                await submitChallengeResponse(blob);

            };

            /*
            * Start recording
            */
            state.recorder.start();
            console.log("🎬 Challenge recording started");


            /*
            * Start browser speech recognition if available
            */
            startChallengeSpeechRecognition();

            updateChallengeStatus(
                "🎤 Listening... Please speak the displayed phrase clearly.",
                "info"
            );

            /*
            * Record for 8 seconds, then automatically verify.
            */
            const recordingDurationMs = 8000;

            state.timer =
                window.setTimeout(() => {

                    if (
                        state.recorder &&
                        state.recorder.state === "recording"
                    ) {

                        console.log(
                            "⏱️ Challenge recording complete. Verifying..."
                        );

                        state.recorder.stop();

                    }

                }, recordingDurationMs);

        } catch (error) {

            console.error(
                "❌ Challenge microphone failed:",
                error
            );

            updateChallengeStatus(
                "Microphone access failed. Please allow microphone permission.",
                "error"
            );

            if (startButton) {
                startButton.disabled = false;
            }

            showChallengeError(
                "Microphone access is required for challenge verification."
            );

        }

    }

    async function submitChallengeResponse(blob) {
        if (!state.challengeId) {
            showChallengeError("Challenge session is missing.");
            return;
        }

        const formData = new FormData();
        formData.append("challenge_id", state.challengeId);
        formData.append("audio", blob, "challenge-response.webm");
        formData.append("transcript", challengeTranscript);

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
            clearTimeout(state.timer);
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
            block: "nearest",
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