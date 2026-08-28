/* ============================================================
   VOICESHIELD AI
   Frontend Application Script
============================================================ */

const API_BASE = "http://127.0.0.1:8000";


/* ============================================================
   DOM ELEMENTS
============================================================ */

const audioInput = document.getElementById("audio-input");
const dropZone = document.getElementById("drop-zone");
const analyzeButton = document.getElementById("analyze-button");
const filePreview = document.getElementById("file-preview");
const fileName = document.getElementById("file-name");
const fileSize = document.getElementById("file-size");
const removeFile = document.getElementById("remove-file");

const initialState = document.getElementById("initial-state");
const loadingState = document.getElementById("loading-state");
const resultState = document.getElementById("result-state");

const metricsSection = document.getElementById("metrics-section");
const riskSection = document.getElementById("risk-section");
const realtimeSection = document.getElementById("realtime-section");

const resultTag = document.getElementById("result-tag");
const predictionBadge = document.getElementById("prediction-badge");
const predictionText = document.getElementById("prediction-text");
const predictionDescription = document.getElementById("prediction-description");
const confidenceValue = document.getElementById("confidence-value");
const confidenceBar = document.getElementById("confidence-bar");

const voiceResult = document.getElementById("voice-result");
const fakeScore = document.getElementById("fake-score");
const fakeScoreBar = document.getElementById("fake-score-bar");

const speakerResult = document.getElementById("speaker-result");
const speakerScore = document.getElementById("speaker-score");
const speakerBar = document.getElementById("speaker-bar");

const contextResult = document.getElementById("context-result");
const contextScore = document.getElementById("context-score");
const contextBar = document.getElementById("context-bar");

const riskScore = document.getElementById("risk-score");
const riskLevel = document.getElementById("risk-level");
const riskAction = document.getElementById("risk-action");
const riskRing = document.getElementById("risk-ring-progress");
const riskReasons = document.getElementById("risk-reasons");
const riskScoreElement = document.getElementById("risk-score");
const chunkTimeline = document.getElementById("chunk-timeline");
const chunkTimelineCard = document.getElementById("chunk-timeline-card");

let selectedFile = null;
let referenceFile = null;


/* ============================================================
   GLASS MOUSE FOLLOW EFFECT
============================================================ */

function initializeGlassInteraction() {

    const cards = document.querySelectorAll(".glass-card");

    if (!cards.length) {
        return;
    }

    /*
     * Disable the effect on touch devices.
     * Mouse tracking is only useful when an actual pointer exists.
     */

    if (
        window.matchMedia("(hover: none)").matches ||
        window.matchMedia("(pointer: coarse)").matches
    ) {
        return;
    }

    cards.forEach((card) => {

        card.addEventListener("mousemove", (event) => {

            const rect = card.getBoundingClientRect();

            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            const percentX = (x / rect.width) * 100;
            const percentY = (y / rect.height) * 100;

            /*
             * Position of the glowing glass light.
             */

            card.style.setProperty(
                "--mouse-x",
                `${percentX}%`
            );

            card.style.setProperty(
                "--mouse-y",
                `${percentY}%`
            );

            /*
             * Moves the reflection according to cursor position.
             */

            card.style.setProperty(
                "--shine-position",
                `${percentX}%`
            );

        });

        card.addEventListener("mouseleave", () => {

            card.style.setProperty(
                "--mouse-x",
                "50%"
            );

            card.style.setProperty(
                "--mouse-y",
                "50%"
            );

            card.style.setProperty(
                "--shine-position",
                "0%"
            );

        });

    });
}


/* ============================================================
   EVENT LISTENERS & DRAG/DROP
============================================================ */

if (dropZone) {

    dropZone.addEventListener("click", () => {

        if (audioInput) {
            audioInput.click();
        }

    });


    dropZone.addEventListener("dragover", (event) => {

        event.preventDefault();

        dropZone.classList.add("dragover");

    });


    dropZone.addEventListener("dragleave", () => {

        dropZone.classList.remove("dragover");

    });


    dropZone.addEventListener("drop", (event) => {

        event.preventDefault();

        dropZone.classList.remove("dragover");

        const file = event.dataTransfer.files[0];

        if (file) {
            selectFile(file);
        }

    });

}


if (audioInput) {

    audioInput.addEventListener("change", (event) => {

        const file = event.target.files[0];

        if (file) {
            selectFile(file);
        }

    });

}


if (removeFile) {

    removeFile.addEventListener("click", () => {

        selectedFile = null;

        if (audioInput) {
            audioInput.value = "";
        }

        if (filePreview) {
            filePreview.classList.add("hidden");
        }

        if (analyzeButton) {
            analyzeButton.disabled = true;
        }
        if (simulateCallButton) {
    simulateCallButton.disabled = true;
        }

        if (liveCallStatus) {
            liveCallStatus.classList.add("hidden");
        }

    });

}


if (analyzeButton) {

    analyzeButton.addEventListener("click", () => {

        if (selectedFile) {

            analyzeAudio(
                selectedFile,
                referenceFile
            );

        } else {

            showFrontendError(
                "Please select an audio file first."
            );

        }

    });

}


/* ============================================================
   FILE SELECTION & UTILITIES
============================================================ */

function selectFile(file) {

    if (!isSupportedAudioFile(file)) {
        selectedFile = null;

        if (filePreview) {
            filePreview.classList.add("hidden");
        }

        if (analyzeButton) {
            analyzeButton.disabled = true;
        }

        showFrontendError(
            "Unsupported recording. Use WAV, MP3, FLAC, OGG, WebM, M4A, AAC, or Opus."
        );

        return;
    }

    selectedFile = file;

    if (fileName) {
        fileName.textContent = file.name;
    }

    if (fileSize) {
        fileSize.textContent =
            formatFileSize(file.size);
    }

    if (filePreview) {
        filePreview.classList.remove("hidden");
    }

    if (analyzeButton) {
        analyzeButton.disabled = false;
    }
    if (simulateCallButton) {
        simulateCallButton.disabled = false;
    }

    setLiveCallStatus(
        "READY",
        "ready"
    );

}

function isSupportedAudioFile(file) {

    if (!file) {
        return false;
    }

    const extension =
        file.name.toLowerCase().match(/\.[^.]+$/)?.[0] || "";

    const supportedExtensions = [
        ".wav",
        ".mp3",
        ".flac",
        ".ogg",
        ".webm",
        ".m4a",
        ".aac",
        ".opus",
        ".oga"
    ];

    const supportedMimeTypes = [
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/flac",
        "audio/ogg",
        "audio/webm",
        "audio/mp4",
        "audio/aac",
        "audio/opus"
    ];

    return (
        supportedExtensions.includes(extension) ||
        supportedMimeTypes.includes(file.type.toLowerCase())
    );
}

function getUploadableAudioFile(file) {

    if (file.name.match(/\.[^.]+$/)) {
        return file;
    }

    const mimeToExtension = {
        "audio/wav": "wav",
        "audio/x-wav": "wav",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/flac": "flac",
        "audio/ogg": "ogg",
        "audio/webm": "webm",
        "audio/mp4": "m4a",
        "audio/aac": "aac",
        "audio/opus": "opus"
    };

    const extension =
        mimeToExtension[file.type.toLowerCase()] || "webm";

    return new File(
        [file],
        `recording.${extension}`,
        { type: file.type || "audio/webm" }
    );
}


function formatFileSize(bytes) {

    if (bytes < 1024) {
        return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}


function formatPercent(value) {

    return (
        Number(value || 0) * 100
    ).toFixed(2) + "%";
}


function escapeHtml(value) {

    const div = document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
}


/* ============================================================
   STATE MANAGEMENT
============================================================ */

function setLoadingState(isLoading) {

    if (isLoading) {

        if (initialState) {
            initialState.classList.add("hidden");
        }

        if (resultState) {
            resultState.classList.add("hidden");
        }

        if (loadingState) {
            loadingState.classList.remove("hidden");
        }

        if (metricsSection) {
            metricsSection.classList.add("hidden");
        }

        if (riskSection) {
            riskSection.classList.add("hidden");
        }

        if (realtimeSection) {
            realtimeSection.classList.add("hidden");
        }

        if (analyzeButton) {

            analyzeButton.disabled = true;

            analyzeButton.classList.add(
                "analyzing"
            );

            const buttonText =
                analyzeButton.querySelector("span:first-child");

            if (buttonText) {
                buttonText.textContent =
                    "ANALYZING...";
            }

        }

        if (resultTag) {
            resultTag.textContent = "ANALYZING";
        }

    } else {

        if (loadingState) {
            loadingState.classList.add("hidden");
        }

        if (analyzeButton) {

            analyzeButton.disabled = false;

            analyzeButton.classList.remove(
                "analyzing"
            );

            const buttonText =
                analyzeButton.querySelector("span:first-child");

            if (buttonText) {
                buttonText.textContent =
                    "ANALYZE VOICE";
            }

        }

    }
}


function showFrontendError(message) {

    setLoadingState(false);

    if (initialState) {
        initialState.classList.add("hidden");
    }

    if (resultState) {
        resultState.classList.remove("hidden");
    }

    if (metricsSection) {
        metricsSection.classList.add("hidden");
    }

    if (riskSection) {
        riskSection.classList.add("hidden");
    }

    if (realtimeSection) {
        realtimeSection.classList.add("hidden");
    }

    if (resultTag) {
        resultTag.textContent = "ERROR";
    }

    if (predictionBadge) {
        predictionBadge.textContent =
            "ANALYSIS ERROR";
    }

    if (predictionText) {
        predictionText.textContent =
            "Unable to analyze audio";
    }

    if (predictionDescription) {
        predictionDescription.textContent =
            message;
    }
}
/* ============================================================
   LIVE CALL ERROR
============================================================ */

/* ============================================================
   LIVE CALL ERROR HANDLER
   ============================================================ */

function showLiveCallError(
    message
) {

    console.error(
        "LIVE CALL ERROR:",
        message
    );

    if (liveCallStatus) {

        liveCallStatus.textContent =
            "LIVE ERROR";

    }

    const processingStatus =
        document.getElementById(
            "live-processing-status"
        );

    if (processingStatus) {

        processingStatus.textContent =
            "LIVE ANALYSIS ERROR";

        processingStatus.classList.remove(
            "processing"
        );

    }

    if (predictionDescription) {

        predictionDescription.textContent =
            message ||
            "Live call analysis encountered an error.";

    }

}

/* ============================================================
   API REQUEST: ANALYZE AUDIO
============================================================ */

async function analyzeAudio(
    file,
    referenceFile = null
) {

    if (!file) {

        showFrontendError(
            "Please select an audio file first."
        );

        return;
    }

    const formData = new FormData();
    const uploadFile = getUploadableAudioFile(file);

    formData.append(
        "audio",
        uploadFile
    );

    formData.append(
        "file",
        uploadFile
    );

    if (referenceFile) {

        formData.append(
            "reference_audio",
            referenceFile
        );

    }

    setLoadingState(true);

    try {

        const response = await fetch(
            `${API_BASE}/api/analyze`,
            {
                method: "POST",
                body: formData
            }
        );

        if (!response.ok) {

            const errorText =
                await response.text();

            throw new Error(
                `Backend error ${response.status}: ${errorText}`
            );

        }

        const data =
            await response.json();

        console.log(
            "BACKEND RESULT:",
            data
        );

        const result =
            data.result || data;

        renderAnalysis(result);

        updateSecurityIntelligence(
            result
        );

        updateThreatAssessment(
            result
        );

        updateSecurityFindings(
            result
        );

        return result;
    } catch (error) {

        console.error(
            "Analysis failed:",
            error
        );

        showFrontendError(
            error.message ||
            "An unexpected network error occurred."
        );

        throw error;

    } finally {

        setLoadingState(false);

    }
}


/* ============================================================
   RENDER ANALYSIS
============================================================ */

function renderAnalysis(data) {

    if (initialState) {
        initialState.classList.add("hidden");
    }

    if (resultState) {
        resultState.classList.remove("hidden");
    }

    if (metricsSection) {
        metricsSection.classList.remove("hidden");
    }

    if (riskSection) {
        riskSection.classList.remove("hidden");
    }

    if (resultTag) {
        resultTag.textContent = "COMPLETE";
    }

    const detection =
        data.voice_detection || {};

    const risk =
        data.risk || {};

    const prediction =
        detection.prediction || "UNKNOWN";

    const confidence =
        Number(
            detection.confidence || 0
        );

    const fake =
        Number(
            detection.fake_score || 0
        );

    if (voiceResult) {
        voiceResult.textContent =
            prediction.toUpperCase();
    }

    if (fakeScore) {
        fakeScore.textContent =
            formatPercent(fake);
    }

    if (fakeScoreBar) {
        fakeScoreBar.style.width =
            `${fake * 100}%`;
    }

    if (confidenceValue) {
        confidenceValue.textContent =
            formatPercent(confidence);
    }

    if (confidenceBar) {
        confidenceBar.style.width =
            `${confidence * 100}%`;
    }

    if (predictionBadge) {

        if (
            prediction.toLowerCase() ===
            "fake"
        ) {

            predictionBadge.textContent =
                "FAKE DETECTED";

            if (predictionText) {
                predictionText.textContent =
                    "Synthetic voice detected";
            }

            if (predictionDescription) {
                predictionDescription.textContent =
                    "The audio contains strong indicators of AI-generated or manipulated speech.";
            }

            predictionBadge.style.color =
                "var(--danger)";

            predictionBadge.style.borderColor =
                "rgba(255,84,112,0.35)";

            predictionBadge.style.background =
                "var(--danger-soft)";

        } else {

            predictionBadge.textContent =
                "REAL";

            if (predictionText) {
                predictionText.textContent =
                    "Authentic voice detected";
            }

            if (predictionDescription) {
                predictionDescription.textContent =
                    "No significant synthetic voice indicators were detected.";
            }

            predictionBadge.style.color =
                "var(--neon)";

            predictionBadge.style.borderColor =
                "var(--border-bright)";

            predictionBadge.style.background =
                "var(--neon-soft)";
        }

    }


    /* Speaker Verification */

    if (data.speaker_verification) {

        const speaker =
            data.speaker_verification;

        const score =
            Number(
                speaker.score || 0
            );

        if (speakerResult) {

            speakerResult.textContent =
                speaker.same_speaker
                    ? "VERIFIED"
                    : "MISMATCH";

        }

        if (speakerScore) {

            speakerScore.textContent =
                score.toFixed(4);

        }

        if (speakerBar) {

            speakerBar.style.width =
                `${Math.min(
                    Math.max(score * 100, 0),
                    100
                )}%`;

        }

    } else {

        if (speakerResult) {
            speakerResult.textContent =
                "N/A";
        }

        if (speakerScore) {
            speakerScore.textContent =
                "Not provided";
        }

        if (speakerBar) {
            speakerBar.style.width =
                "0%";
        }

    }


    /* Context */

    const contextRisk =
        Number(
            data.context_risk_score ??
            data.context?.risk_score ??
            0
        );

    if (contextResult) {

        contextResult.textContent =
            contextRisk >= 0.7
                ? "HIGH"
                : contextRisk >= 0.4
                    ? "MEDIUM"
                    : "LOW";

    }

    if (contextScore) {

        contextScore.textContent =
            formatPercent(contextRisk);

    }

    if (contextBar) {

        contextBar.style.width =
            `${contextRisk * 100}%`;

    }


    /* Risk Styling */

    if (risk.level) {

        applyRiskStyle(
            risk.level
        );

    }


    /* Timeline */

    if (
        data.realtime &&
        Array.isArray(
            data.realtime.chunks
        )
    ) {

        renderChunks(
            data.realtime.chunks
        );

        if (realtimeSection) {
            realtimeSection.classList.remove(
                "hidden"
            );
        }

    }

}


/* ============================================================
   SECURITY INTELLIGENCE
============================================================ */

function updateSecurityIntelligence(result) {

    const detection =
        result.voice_detection || {};

    const speaker =
        result.speaker_verification || {};

    const context =
        result.context || {};

    const prediction =
        detection.prediction || "UNKNOWN";

    const fakeScore =
        Number(
            detection.fake_score || 0
        );

    const authenticityElement =
        document.getElementById(
            "voice-authenticity"
        );

    const fakeProbabilityElement =
        document.getElementById(
            "fake-probability"
        );

    if (authenticityElement) {

        authenticityElement.textContent =
            prediction.toUpperCase();

        authenticityElement.className =
            `status-value ${prediction.toLowerCase()}`;

    }

    if (fakeProbabilityElement) {

        fakeProbabilityElement.textContent =
            `${(
                fakeScore * 100
            ).toFixed(2)}%`;

    }


    const speakerElement =
        document.getElementById(
            "speaker-identity"
        );

    const verificationElement =
        document.getElementById(
            "speaker-verification"
        );

    if (speakerElement) {

        if (
            speaker.same_speaker === true
        ) {

            speakerElement.textContent =
                "VERIFIED";

        } else if (
            speaker.same_speaker === false
        ) {

            speakerElement.textContent =
                "MISMATCH";

        } else {

            speakerElement.textContent =
                "N/A";

        }

    }

    if (verificationElement) {

        if (
            speaker.score !== undefined
        ) {

            verificationElement.textContent =
                `Similarity ${(
                    Number(speaker.score) * 100
                ).toFixed(1)}%`;

        } else {

            verificationElement.textContent =
                "Not provided";

        }

    }


    const contextElement =
        document.getElementById(
            "context-risk"
        );

    const contextThreatElement =
        document.getElementById(
            "context-threat"
        );

    const contextScore =
        Number(
            result.context_risk_score ??
            context.context_risk_score ??
            context.risk_score ??
            0
        );

    if (contextElement) {

        if (contextScore >= 0.7) {

            contextElement.textContent =
                "HIGH";

        } else if (contextScore >= 0.4) {

            contextElement.textContent =
                "MEDIUM";

        } else {

            contextElement.textContent =
                "LOW";

        }

    }

    if (contextThreatElement) {

        contextThreatElement.textContent =
            `${(
                contextScore * 100
            ).toFixed(2)}%`;

    }

}


/* ============================================================
   THREAT ASSESSMENT
============================================================ */

function updateThreatAssessment(result) {

    const risk =
        result.risk || {};

    const score =
        Number(
            risk.score || 0
        );

    const level =
        (
            risk.level || "LOW"
        ).toUpperCase();

    const action =
        (
            risk.action || "ALLOW"
        ).toUpperCase();

    const reasons = Array.isArray(risk.reasons)
        ? risk.reasons
        : [];

    const scoreElement =
        document.getElementById(
            "risk-score"
        );

    const levelElement =
        document.getElementById(
            "risk-level"
        );

    const actionElement =
        document.getElementById(
            "risk-action"
        );

    if (scoreElement) {
        scoreElement.textContent =
            Math.round(score);
    }

    if (levelElement) {
        levelElement.textContent =
            `${level} RISK`;
    }

    if (actionElement) {
        actionElement.textContent =
            action;
    }


    /*
     * Your HTML uses:
     * #risk-ring-progress
     *
     * So update that element directly.
     */

    const riskCircle =
        document.getElementById(
            "risk-ring-progress"
        );

    if (riskCircle) {

        const circumference =
            578;

        const safeScore =
            Math.min(
                Math.max(score, 0),
                100
            );

        const offset =
            circumference -
            (safeScore / 100) *
            circumference;

        riskCircle.style.strokeDashoffset =
            offset;

    }

}


/* ============================================================
   SECURITY FINDINGS
============================================================ */

function updateSecurityFindings(result) {

    const risk =
        result.risk || {};

    const reasons =
        Array.isArray(risk.reasons)
            ? risk.reasons
            : [];

    const findingsContainer =
        document.getElementById(
            "security-findings"
        );

    if (!findingsContainer) {
        return;
    }

    findingsContainer.innerHTML = "";


    if (reasons.length === 0) {

        findingsContainer.innerHTML = `
            <div class="finding safe">
                <span class="finding-icon">✓</span>
                <span>No significant security risk detected.</span>
            </div>
        `;

        return;
    }


    reasons.forEach((reason) => {

        const finding =
            document.createElement("div");

        finding.className =
            "finding";

        finding.innerHTML = `
            <span class="finding-icon">!</span>
            <span>${escapeHtml(reason)}</span>
        `;

        findingsContainer.appendChild(
            finding
        );

    });

}


/* ============================================================
   RISK STYLING
============================================================ */

function applyRiskStyle(level) {

    const normalized =
        String(level).toUpperCase();

    if (
        !riskLevel ||
        !riskAction ||
        !riskRing
    ) {
        return;
    }


    if (normalized === "HIGH") {

        riskLevel.style.color =
            "var(--danger)";

        riskAction.style.color =
            "var(--danger)";

        riskAction.style.borderColor =
            "rgba(255,84,112,0.35)";

        riskAction.style.background =
            "var(--danger-soft)";

        riskRing.style.stroke =
            "var(--danger)";

    } else if (
        normalized === "MEDIUM"
    ) {

        riskLevel.style.color =
            "var(--warning)";

        riskAction.style.color =
            "var(--warning)";

        riskAction.style.borderColor =
            "rgba(255,209,102,0.35)";

        riskAction.style.background =
            "var(--warning-soft)";

        riskRing.style.stroke =
            "var(--warning)";

    } else {

        riskLevel.style.color =
            "var(--neon)";

        riskAction.style.color =
            "var(--neon)";

        riskAction.style.borderColor =
            "var(--border-bright)";

        riskAction.style.background =
            "var(--neon-soft)";

        riskRing.style.stroke =
            "var(--neon)";

    }

}


/* ============================================================
   REALTIME CHUNKS
============================================================ */

function renderChunks(chunks) {

    if (!chunkTimeline) {
        return;
    }

    chunkTimeline.innerHTML = "";


    chunks.forEach((chunk) => {

        const element =
            document.createElement("div");

        const fake =
            String(
                chunk.prediction
            ).toLowerCase() === "fake";

        element.className =
            fake
                ? "chunk fake"
                : "chunk";

        element.innerHTML = `
            <div class="chunk-index">
                CHUNK ${
                    String(
                        chunk.chunk_index + 1
                    ).padStart(2, "0")
                }
            </div>

            <div class="chunk-prediction">
                ${
                    String(
                        chunk.prediction
                    ).toUpperCase()
                }
            </div>

            <div class="chunk-score">
                ${
                    formatPercent(
                        chunk.confidence
                    )
                } confidence
            </div>
        `;

        chunkTimeline.appendChild(
            element
        );

    });

}


/* ============================================================
   HEALTH CHECK
============================================================ */

async function checkSystemHealth() {

    try {

        const response =
            await fetch(
                `${API_BASE}/api/health`
            );

        const data =
            await response.json();

        const status =
            document.getElementById(
                "system-status"
            );

        if (status) {

            if (
                data.status === "online" &&
                data.firewall
            ) {

                status.textContent =
                    "ONLINE";

            } else {

                status.textContent =
                    "DEGRADED";

            }

        }

    } catch (error) {

        const status =
            document.getElementById(
                "system-status"
            );

        if (status) {
            status.textContent =
                "OFFLINE";
        }

        console.error(
            "Health check failed:",
            error
        );

    }

}
/* ============================================================
   LIVE MICROPHONE VISUALIZER
============================================================ */
let liveAnalyser = null;
let liveMicrophoneSource = null;
let liveWaveformAnimation = null;
let liveAudioContext = null;
let liveVoiceHighpass = null;
let liveVoiceLowpass = null;
function startLiveVisualizer(stream) {

    const canvas =
        document.getElementById("live-waveform");

    const container =
        document.querySelector(".live-waveform-container");

    const listeningText =
        document.getElementById("live-listening-text");

    const processingStatus =
        document.getElementById("live-processing-status");

    if (!canvas || !stream) {
        return;
    }

    const ctx =
        canvas.getContext("2d");

    liveAudioContext =
        new (window.AudioContext || window.webkitAudioContext)();

    liveAnalyser =
        liveAudioContext.createAnalyser();

    liveAnalyser.fftSize = 512;
    liveAnalyser.smoothingTimeConstant = 0.9;

    liveVoiceHighpass =
        liveAudioContext.createBiquadFilter();

    liveVoiceHighpass.type = "highpass";
    liveVoiceHighpass.frequency.value = 120;
    liveVoiceHighpass.Q.value = 0.7;

    liveVoiceLowpass =
        liveAudioContext.createBiquadFilter();

    liveVoiceLowpass.type = "lowpass";
    liveVoiceLowpass.frequency.value = 4200;
    liveVoiceLowpass.Q.value = 0.7;

    liveMicrophoneSource =
        liveAudioContext.createMediaStreamSource(stream);

    liveMicrophoneSource.connect(liveVoiceHighpass);
    liveVoiceHighpass.connect(liveVoiceLowpass);
    liveVoiceLowpass.connect(liveAnalyser);

    const bufferLength =
        liveAnalyser.fftSize;

    const dataArray =
        new Uint8Array(bufferLength);

    function resizeCanvas() {

        const rect =
            canvas.getBoundingClientRect();

        const ratio =
            window.devicePixelRatio || 1;

        canvas.width =
            rect.width * ratio;

        canvas.height =
            rect.height * ratio;

        ctx.setTransform(
            ratio,
            0,
            0,
            ratio,
            0,
            0
        );
    }

    resizeCanvas();

    window.addEventListener(
        "resize",
        resizeCanvas
    );

    if (container) {
        container.classList.add("listening");
    }

    if (listeningText) {
        listeningText.textContent =
            "LISTENING";
    }

    if (processingStatus) {
        processingStatus.textContent =
            "Microphone active - analyzing live audio";
    }

    function draw() {

        liveWaveformAnimation =
            requestAnimationFrame(draw);

        const width =
            canvas.clientWidth;

        const height =
            canvas.clientHeight;

        const center =
            height / 2;

        liveAnalyser.getByteTimeDomainData(
            dataArray
        );

        let sumSquares = 0;

        for (let i = 0; i < bufferLength; i++) {
            const deviation =
                (dataArray[i] - 128) / 128;

            sumSquares += deviation * deviation;
        }

        const voiceEnergy =
            Math.sqrt(sumSquares / bufferLength);

        const voiceDetected =
            voiceEnergy > 0.025;

        ctx.clearRect(
            0,
            0,
            width,
            height
        );

        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
        ctx.lineWidth = 1;
        ctx.stroke();

        const points = [];
        const sliceWidth = width / (bufferLength - 1);
        const displayGain = voiceDetected ? 4.5 : 0.35;

        for (let i = 0; i < bufferLength; i++) {
            const deviation =
                (dataArray[i] - 128) / 128;

            const visualDeviation =
                deviation * displayGain;

            points.push({
                x: i * sliceWidth,
                y: Math.max(
                    4,
                    Math.min(
                        height - 4,
                        center + visualDeviation * center
                    )
                )
            });
        }

        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);

        for (let i = 1; i < points.length - 1; i++) {
            const midpointX =
                (points[i].x + points[i + 1].x) / 2;

            const midpointY =
                (points[i].y + points[i + 1].y) / 2;

            ctx.quadraticCurveTo(
                points[i].x,
                points[i].y,
                midpointX,
                midpointY
            );
        }

        const lastPoint =
            points[points.length - 1];

        ctx.quadraticCurveTo(
            lastPoint.x,
            lastPoint.y,
            lastPoint.x,
            lastPoint.y
        );

        ctx.shadowColor =
            getComputedStyle(document.documentElement)
                .getPropertyValue("--neon")
                .trim() || "#00ffcc";

        ctx.strokeStyle = ctx.shadowColor;
        ctx.shadowBlur = 8;

        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.shadowBlur = 0;
    }

    draw();
}

function stopLiveVisualizer() {

    if (liveWaveformAnimation) {

        cancelAnimationFrame(
            liveWaveformAnimation
        );

        liveWaveformAnimation =
            null;
    }

    if (liveMicrophoneSource) {

        try {
            liveMicrophoneSource.disconnect();
        } catch (error) {}

        liveMicrophoneSource = null;
    }

    if (liveVoiceHighpass) {
        liveVoiceHighpass.disconnect();
        liveVoiceHighpass = null;
    }

    if (liveVoiceLowpass) {
        liveVoiceLowpass.disconnect();
        liveVoiceLowpass = null;
    }

    if (liveAnalyser) {
        liveAnalyser = null;
    }

    if (liveAudioContext) {

        try {
            liveAudioContext.close();
        } catch (_) {}

        liveAudioContext = null;
    }

    const canvas =
        document.getElementById(
            "live-waveform"
        );

    if (canvas) {

        const ctx =
            canvas.getContext("2d");

        ctx.clearRect(
            0,
            0,
            canvas.width,
            canvas.height
        );
    }

    const container =
        document.querySelector(".live-waveform-container");

    const listeningText =
        document.getElementById("live-listening-text");

    const processingStatus =
        document.getElementById("live-processing-status");

    if (container) {
        container.classList.remove("listening");
    }

    if (listeningText) {
        listeningText.textContent =
            "READY";
    }

    if (processingStatus) {
        processingStatus.textContent =
            "Microphone inactive";
    }

}

/* ============================================================
   LIVE CALL DETECTION
   Phase 2
============================================================ */

const liveCallButton =
    document.getElementById("live-call-button");

const liveCallStatus =
    document.getElementById("live-call-control-status");

const liveCallPanel =
    document.getElementById("live-call-panel");

const livePrediction =
    document.getElementById("live-prediction");

const liveFakeScore =
    document.getElementById("live-fake-score");

const liveRiskScore =
    document.getElementById("live-risk-score");

const liveAction =
    document.getElementById("live-action");

const liveTimeline =
    document.getElementById("live-timeline");

const liveDuration =
    document.getElementById("live-call-duration");


let liveSocket = null;
let liveMediaStream = null;
let liveProcessor = null;
let liveSource = null;

let liveRunning = false;
let liveStartTime = null;
let liveTimer = null;
/* ============================================================
   LIVE MICROPHONE STATE
============================================================ */

let liveCallActive = false;
let liveMediaRecorder = null;
let liveChunkTimer = null;
/* ============================================================
   LIVE TRANSCRIPTION
   Browser speech recognition
   ============================================================ */
let liveSpeechRecognition = null;
let liveTranscriptFinal = "";
let liveTranscriptInterim = "";
let liveProviderTranscript = "";
let liveTranscriptProvider = null;
let liveSpeechSupported = false;
// Tracks whether SpeechRecognition should remain active
// because the VoiceShield call is still running.
let liveSpeechShouldRun = false;

// Prevents multiple simultaneous restart timers.
let liveSpeechRestartTimer = null;
let liveTranscriptBoxShowing = false;
/* ============================================================
   INITIALIZE LIVE TRANSCRIPTION
   ============================================================ */
function initializeLiveTranscription() {
    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    /*
     * Browser does not support Web Speech API.
     */
    if (!SpeechRecognition) {
        console.warn(
            "Speech Recognition API is not supported by this browser."
        );

        liveSpeechSupported = false;

        updateLiveTranscriptStatus(
            "TRANSCRIPTION UNAVAILABLE"
        );

        return;
    }

    liveSpeechSupported = true;

    /*
     * If an older recognition instance exists,
     * stop it before creating a new one.
     */
    if (liveSpeechRecognition) {
        try {
            liveSpeechRecognition.onend = null;
            liveSpeechRecognition.onerror = null;
            liveSpeechRecognition.onresult = null;
            liveSpeechRecognition.stop();
        } catch (error) {
            console.warn(
                "Previous speech recognition cleanup warning:",
                error
            );
        }
    }

    /*
     * Create a fresh recognition instance.
     */
    liveSpeechRecognition =
        new SpeechRecognition();

    /*
     * Keep recognition continuous while the call is active.
     */
    liveSpeechRecognition.continuous = true;

    /*
     * Show words while the caller is speaking.
     */
    liveSpeechRecognition.interimResults = true;

    /*
     * Indian English is appropriate for your current project.
     */
    liveSpeechRecognition.lang = "en-IN";

    /*
     * ------------------------------------------------------------
     * RECOGNITION STARTED
     * ------------------------------------------------------------
     */
    liveSpeechRecognition.onstart = () => {
        console.log(
            "LIVE TRANSCRIPTION STARTED"
        );

        updateLiveTranscriptStatus(
            "LISTENING FOR SPEECH"
        );
    };

    /*
     * ------------------------------------------------------------
     * SPEECH RESULT
     * ------------------------------------------------------------
     *
     * This is where the ACTUAL WORDS are received.
     */
    liveSpeechRecognition.onresult = (event) => {
        let finalText = "";
        let interimText = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {
            const transcript =
                event.results[i][0]?.transcript || "";

            if (
                event.results[i].isFinal
            ) {
                finalText +=
                    transcript + " ";
            } else {
                interimText +=
                    transcript;
            }
        }

        /*
         * Store confirmed speech permanently.
         */
        if (finalText.trim()) {
            liveTranscriptFinal +=
                finalText + " ";
        }

        /*
         * Store currently spoken/interim text.
         */
        liveTranscriptInterim =
            interimText;

        /*
         * Immediately refresh the visible transcript.
         */
        updateLiveTranscriptDisplay();

        console.log(
            "LIVE TRANSCRIPT:",
            finalText || interimText
        );
    };

    /*
     * ------------------------------------------------------------
     * RECOGNITION ERROR
     * ------------------------------------------------------------
     */
    liveSpeechRecognition.onerror = (event) => {
        const error =
            event?.error || "unknown";

        console.warn(
            "Live transcription warning:",
            error
        );

        /*
         * Permission problems cannot be fixed by restarting.
         */
        if (
            error === "not-allowed" ||
            error === "service-not-allowed"
        ) {
            liveSpeechShouldRun = false;

            updateLiveTranscriptStatus(
                error === "not-allowed"
                    ? "MICROPHONE PERMISSION REQUIRED"
                    : "SPEECH SERVICE UNAVAILABLE"
            );

            return;
        }

        /*
         * "no-speech" is NOT a fatal error.
         *
         * The caller may simply have paused.
         */
        if (
            error === "no-speech"
        ) {
            updateLiveTranscriptStatus(
                "LISTENING FOR SPEECH"
            );

            return;
        }

        /*
         * Network/service errors are recoverable.
         */
        if (
            error === "network" ||
            error === "aborted" ||
            error === "audio-capture"
        ) {
            updateLiveTranscriptStatus(
                "SPEECH SERVICE RECONNECTING..."
            );

            scheduleLiveSpeechRestart();

            return;
        }

        /*
         * Unknown errors should not kill the
         * VoiceShield security analysis.
         */
        console.warn(
            "Unhandled speech recognition error:",
            error
        );

        scheduleLiveSpeechRestart();
    };

    /*
     * ------------------------------------------------------------
     * RECOGNITION ENDED
     * ------------------------------------------------------------
     *
     * Chrome may terminate SpeechRecognition automatically.
     * If the call is still active, restart it.
     */
    liveSpeechRecognition.onend = () => {
        console.log(
            "LIVE TRANSCRIPTION ENDED"
        );

        /*
         * Do NOT restart after the user has ended
         * the VoiceShield call.
         */
        if (!liveSpeechShouldRun) {
            return;
        }

        scheduleLiveSpeechRestart();
    };
}

/*
 * ============================================================
 * RESTART LIVE SPEECH RECOGNITION
 * ============================================================
 *
 * Chrome's SpeechRecognition service can terminate unexpectedly.
 * This function safely starts a new recognition session while
 * the VoiceShield call is still active.
 */
function scheduleLiveSpeechRestart() {
    /*
     * Never restart if the call has already ended.
     */
    if (!liveSpeechShouldRun) {
        return;
    }

    /*
     * Prevent multiple restart timers from being created.
     */
    if (liveSpeechRestartTimer) {
        return;
    }

    liveSpeechRestartTimer =
        setTimeout(() => {
            liveSpeechRestartTimer = null;

            /*
             * The user may have ended the call while
             * the timer was waiting.
             */
            if (!liveSpeechShouldRun) {
                return;
            }

            try {
                /*
                 * Create a fresh recognition object.
                 *
                 * This is more reliable than repeatedly
                 * calling start() on an ended instance.
                 */
                initializeLiveTranscription();

                if (
                    liveSpeechRecognition
                ) {
                    liveSpeechRecognition.start();

                    console.log(
                        "LIVE TRANSCRIPTION RESTARTED"
                    );
                }
            } catch (error) {
                console.warn(
                    "Transcription restart failed:",
                    error
                );

                /*
                 * Try again after a short delay.
                 */
                scheduleLiveSpeechRestart();
            }
        }, 500);
}
/* ============================================================
   LIVE TRANSCRIPT DISPLAY
   ------------------------------------------------------------
   Creates a compact transcript panel inside the existing
   live-call area. No HTML structure changes are required.
============================================================ */

function updateLiveTranscriptDisplay() {

    /*
     * Prefer the existing live monitor.
     * If it is unavailable, fall back to the live call panel.
     */

    const monitor =
        document.getElementById(
            "vs-live-transcript"
        ) ||
        document.querySelector(
            ".vs-live-monitor"
        ) ||
        liveCallPanel;

    if (!monitor) {
        console.warn(
            "Live transcript target container not found."
        );

        return;
    }

    let transcriptBox =
        document.getElementById(
            "vs-live-transcript"
        );

    /*
     * Create the transcript element once.
     */

    if (!transcriptBox) {

        transcriptBox =
            document.createElement(
                "div"
            );

        transcriptBox.id =
            "vs-live-transcript";

        transcriptBox.setAttribute(
            "aria-live",
            "polite"
        );

        /*
         * Keep the existing visual language.
         * No new page structure is introduced.
         */

        transcriptBox.style.marginTop =
            "12px";

        transcriptBox.style.padding =
            "10px 12px";

        transcriptBox.style.borderTop =
            "1px solid rgba(255,255,255,0.06)";

        transcriptBox.style.fontSize =
            "12px";

        transcriptBox.style.lineHeight =
            "1.6";

        transcriptBox.style.opacity =
            "0.9";

        transcriptBox.style.minHeight =
            "22px";

        transcriptBox.style.maxHeight =
            "90px";

        transcriptBox.style.overflowY =
            "auto";

        monitor.appendChild(
            transcriptBox
        );
    }


    const finalText =
        String(
            liveProviderTranscript || liveTranscriptFinal || ""
        ).trim();

    const interimText =
        liveProviderTranscript
            ? ""
            : String(liveTranscriptInterim || "").trim();


    /*
     * Nothing spoken yet.
     */

    if (
        !finalText &&
        !interimText
    ) {

        transcriptBox.innerHTML =
            `
            <div style="
                font-size:9px;
                letter-spacing:0.12em;
                opacity:0.5;
                margin-bottom:4px;
            ">
                LIVE TRANSCRIPT
            </div>

            <div style="
                opacity:0.45;
            ">
                Listening for speech...
            </div>
            `;

        return;
    }


    /*
     * Final speech is normal.
     * Interim speech is slightly faded.
     */

    transcriptBox.innerHTML =
        `
        <div style="
            font-size:9px;
            letter-spacing:0.12em;
            opacity:0.5;
            margin-bottom:4px;
        ">
            LIVE TRANSCRIPT
        </div>

        <div>
            ${escapeHtml(finalText)}

            <span style="
                opacity:0.45;
            ">
                ${escapeHtml(interimText)}
            </span>
        </div>
        `;
}

function appendProviderTranscript(transcription) {
    const text = String(
        transcription?.transcript || ""
    ).trim();

    if (!text) {
        return;
    }

    liveTranscriptProvider =
        transcription.provider || liveTranscriptProvider;
    liveProviderTranscript =
        `${liveProviderTranscript} ${text}`.trim();
    updateLiveTranscriptDisplay();
}


function updateLiveTranscriptStatus(
    message
) {

    const transcriptBox =
        document.getElementById(
            "vs-live-transcript"
        );

    if (!transcriptBox) {
        return;
    }

    let statusElement =
        transcriptBox.querySelector(
            "[data-transcript-status]"
        );

    if (!statusElement) {
        statusElement =
            document.createElement("div");
        statusElement.setAttribute(
            "data-transcript-status",
            "true"
        );
        statusElement.style.marginTop =
            "5px";
        statusElement.style.fontSize =
            "9px";
        statusElement.style.opacity =
            "0.45";
        transcriptBox.appendChild(
            statusElement
        );
    }

    statusElement.textContent = message;

}
/* ============================================================
   FINAL SECURITY REASON
   ============================================================ */

function updateLiveFinalReason(
    verdict,
    reasons
) {

    const monitor =
        document.querySelector(
            ".vs-live-monitor"
        );

    if (!monitor) {
        return;
    }

    let reasonBox =
        document.getElementById(
            "vs-live-final-reason"
        );

    /*
     * Create once.
     */

    if (!reasonBox) {

        reasonBox =
            document.createElement(
                "div"
            );

        reasonBox.id =
            "vs-live-final-reason";

        reasonBox.style.marginTop =
            "14px";

        reasonBox.style.padding =
            "12px 14px";

        reasonBox.style.borderRadius =
            "12px";

        reasonBox.style.background =
            "rgba(255,255,255,0.025)";

        reasonBox.style.border =
            "1px solid rgba(255,255,255,0.07)";

        monitor.appendChild(
            reasonBox
        );

    }


    const safe =
        verdict === "SAFE";


    reasonBox.innerHTML = `
        <div style="
            font-size:9px;
            letter-spacing:0.14em;
            opacity:0.5;
            margin-bottom:6px;
        ">
            FINAL SECURITY ASSESSMENT
        </div>

        <div style="
            font-size:13px;
            font-weight:700;
            margin-bottom:7px;
        ">
            ${safe ? "✓ SAFE" : "⚠ UNSAFE"}
        </div>

        <div style="
            font-size:11px;
            line-height:1.7;
            opacity:0.72;
        ">
            ${reasons
                .map(
                    reason =>
                        `<div>• ${escapeHtml(reason)}</div>`
                )
                .join("")}
        </div>
    `;

}
let liveChunkIndex = 0;
let liveDisplayedChunkCount = 0;
let liveCallStartedAt = null;
let liveCallTimer = null;
let liveProcessing = false;
let liveChunksProcessed = 0;
let liveRiskHistory = [];
let livePendingAnalyses = 0;
let liveStableNotificationSent = false;
let liveNotificationSource = null;
let liveDecisionMade = false;

/* ============================================================
   LIVE RESULT STABILITY ENGINE
   Prevents one noisy/misclassified chunk from
   immediately declaring the entire call FAKE.
============================================================ */

let livePredictionHistory = [];
/*
 * ALL processed chunk results for this call.
 *
 * IMPORTANT:
 * livePredictionHistory is intentionally limited to the latest
 * 4 chunks for real-time stability.
 *
 * liveAllPredictionHistory is NEVER truncated during the call.
 * It is used for the final call-level decision.
 */
let liveAllPredictionHistory = [];

/*
 * Current real-time security state.
 *
 * This is separate from the final decision.
 */
let liveSecurityState = "analyzing";

/*
 * Prevent repeated high-risk notifications.
 *
 * We do not want to spam the user on every chunk.
 */
let liveHighRiskNotificationSent = false;
let liveSuspiciousNotificationSent = false;
/*
 * ============================================================
 * LIVE RESULT STABILITY
 * ============================================================
 *
 * A single chunk NEVER decides the live security state.
 *
 * VoiceShield uses the latest 4 processed chunks as a
 * rolling evidence window for real-time security decisions.
 *
 * IMPORTANT:
 * A stable LIVE result is NOT the final call decision.
 * The final call decision is calculated separately from
 * liveAllPredictionHistory when the call/stream ends.
 * ============================================================
 */

const LIVE_STABILITY_WINDOW = 4;
const LIVE_FAKE_THRESHOLD = 0.85;
const LIVE_STABLE_REQUIRED = 4;

let liveStablePrediction = "unknown";
let liveStableFakeScore = 0;
let liveStableRiskScore = 0;
function updateLiveListeningState(listening = true) {

    const indicator =
        document.querySelector(
            ".live-listening-indicator"
        );

    const status =
        document.getElementById(
            "live-call-status"
        );

    if (indicator) {
        indicator.classList.toggle(
            "active",
            listening
        );
    }

    if (status) {
        status.textContent =
            listening
                ? "LISTENING"
                : "PAUSED";
    }
}

function updateLiveProcessingState(processing = true) {

    const status =
        document.getElementById(
            "live-processing-status"
        );

    if (!status) {
        return;
    }

    status.textContent =
        processing
            ? "ANALYZING"
            : "LISTENING";

    status.classList.toggle(
        "processing",
        processing
    );
    if (processing) {

    showLiveSecurityAnalyzing();

}
}
/* ============================================================
   LIVE SECURITY ANALYSIS STATE
   ------------------------------------------------------------
   Keeps the main security status neutral while the
   live detector is still collecting evidence.
   The REAL/FAKE decision is shown only after stability.
============================================================ */

function showLiveSecurityAnalyzing() {

    /*
     * Never show a fake/real final verdict while
     * the stability engine is still collecting chunks.
     */

    document.body.classList.remove(
        "security-danger",
        "security-success",
        "security-warning"
    );

    if (resultTag) {
        resultTag.textContent =
            "LIVE • ANALYZING";
    }

    if (predictionBadge) {
        predictionBadge.innerHTML = `
            <div class="live-analysis-loader">
                <div class="matrix-loader" aria-hidden="true"></div>
                <div class="live-analysis-label">ANALYZING VOICE</div>
            </div>
        `;

        predictionBadge.className =
            "prediction-badge live live-analyzing";
    }

    if (predictionText) {

        predictionText.textContent =
            "Analyzing live call";
    }

    if (predictionDescription) {

        predictionDescription.textContent =
            "VoiceShield is collecting multiple voice segments before making a security decision.";
    }

    if (riskLevel) {

        riskLevel.textContent =
            "ANALYZING";
    }

    if (riskAction) {

        riskAction.textContent =
            "MONITOR";
    }
}

function updateLiveSecurityStatus(active) {

    if (active) {

        if (initialState) {
            initialState.classList.add("hidden");
        }

        if (resultState) {
            resultState.classList.remove("hidden");
        }

        showLiveSecurityAnalyzing();

        return;
    }

    if (resultTag) {
        resultTag.textContent = "READY";
    }

    if (predictionBadge) {
        predictionBadge.textContent = "LIVE CALL ENDED";
        predictionBadge.className = "prediction-badge";
    }

    if (predictionText) {
        predictionText.textContent = "Live monitoring stopped";
    }

    if (predictionDescription) {
        predictionDescription.textContent =
            "The call timeline and final detections remain available below.";
    }
}

function startLiveCallTimer() {

    liveCallStartedAt = Date.now();

    const timerElement =
        document.getElementById(
            "live-call-duration"
        ) || document.getElementById(
            "live-duration"
        );

    function updateTimer() {

        if (!liveCallStartedAt || !timerElement) {
            return;
        }

        const elapsed =
            Math.floor(
                (Date.now() - liveCallStartedAt) / 1000
            );

        const minutes =
            Math.floor(elapsed / 60)
                .toString()
                .padStart(2, "0");

        const seconds =
            (elapsed % 60)
                .toString()
                .padStart(2, "0");

        timerElement.textContent =
            `${minutes}:${seconds}`;
    }

    updateTimer();

    clearInterval(liveCallTimer);

    liveCallTimer =
        setInterval(
            updateTimer,
            1000
        );
}

function stopLiveCallTimer() {

    clearInterval(liveCallTimer);
    liveCallTimer = null;
    liveCallStartedAt = null;
}

function recordLiveRisk(riskScore) {

    const score =
        Math.max(
            0,
            Math.min(
                Number(riskScore) || 0,
                100
            )
        );

    liveRiskHistory.push({
        time: Date.now(),
        score
    });

    if (liveRiskHistory.length > 60) {
        liveRiskHistory.shift();
    }

    updateLiveRiskTrend();
}

function updateLiveRiskTrend() {

    const trend =
        document.getElementById(
            "live-risk-trend"
        );

    if (!trend || liveRiskHistory.length < 2) {
        return;
    }

    const latest =
        liveRiskHistory[liveRiskHistory.length - 1].score;

    const previous =
        liveRiskHistory[liveRiskHistory.length - 2].score;

    if (latest > previous + 8) {
        trend.textContent = "RISK ESCALATING";
        trend.className = "risk-trend escalating";
    } else if (latest < previous - 8) {
        trend.textContent = "RISK DECLINING";
        trend.className = "risk-trend declining";
    } else {
        trend.textContent = "RISK STABLE";
        trend.className = "risk-trend stable";
    }
}

async function startLiveCall() {

    if (liveRunning) {
        return;
    }

    try {

        liveMediaStream =
            await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            startLiveVisualizer(liveMediaStream);
            /*
 * Start browser transcription independently
 * from the deepfake detection pipeline.
 */

liveTranscriptFinal = "";
liveTranscriptInterim = "";
liveProviderTranscript = "";
liveTranscriptProvider = null;
initializeLiveTranscription();

if (
    liveSpeechRecognition &&
    liveSpeechSupported
) {
    try {
        liveSpeechRecognition.start();
    } catch (error) {
        console.warn(
            "Live transcription start skipped:",
            error
        );
    }
}

updateLiveTranscriptDisplay();
        liveSocket =
            new WebSocket(
                "ws://127.0.0.1:8000/ws/live-call"
            );

        liveSocket.binaryType = "arraybuffer";

        liveSocket.onopen = () => {

            console.log(
                "LIVE CALL WEBSOCKET CONNECTED"
            );

            beginLiveAudio();

            liveRunning = true;

            updateLiveButton();

            if (liveCallPanel) {
                liveCallPanel.classList.remove(
                    "hidden"
                );
            }

            if (liveTimeline) {
                liveTimeline.innerHTML = "";
            }

            liveStartTime =
                Date.now();

            startLiveTimer();
        };


        liveSocket.onmessage = (event) => {

            try {

                const data =
                    JSON.parse(event.data);

                handleLiveEvent(data);

            } catch (error) {

                console.error(
                    "Invalid live event:",
                    error
                );

            }

        };


        liveSocket.onerror = (error) => {

            console.error(
                "LIVE CALL ERROR:",
                error
            );

            stopLiveCall(
                "Connection error"
            );

        };


        liveSocket.onclose = () => {

            console.log(
                "LIVE CALL WEBSOCKET CLOSED"
            );

            cleanupLiveAudio();

        };

    } catch (error) {

        console.error(
            "Microphone access failed:",
            error
        );

        showFrontendError(
            "Microphone access is required for Live Call Detection."
        );

    }
}

function beginLiveAudio() {

    liveAudioContext =
        new AudioContext();

    liveSource =
        liveAudioContext.createMediaStreamSource(
            liveMediaStream
        );

    /*
     * ScriptProcessor is intentionally used here
     * because it keeps Phase 2 simple and browser-compatible.
     */

    liveProcessor =
        liveAudioContext.createScriptProcessor(
            4096,
            1,
            1
        );

    liveProcessor.onaudioprocess =
        (event) => {

            if (
                !liveSocket ||
                liveSocket.readyState !== WebSocket.OPEN
            ) {
                return;
            }

            const input =
                event.inputBuffer.getChannelData(0);

            const pcm =
                convertFloat32ToPCM16(
                    input
                );

            liveSocket.send(pcm.buffer);
        };

    liveSource.connect(
        liveProcessor
    );

    liveProcessor.connect(
        liveAudioContext.destination
    );
}
function convertFloat32ToPCM16(input) {

    const output =
        new Int16Array(
            input.length
        );

    for (
        let i = 0;
        i < input.length;
        i++
    ) {

        const sample =
            Math.max(
                -1,
                Math.min(
                    1,
                    input[i]
                )
            );

        output[i] =
            sample < 0
                ? sample * 0x8000
                : sample * 0x7FFF;
    }

    return output;
}

function handleLiveEvent(data) {

    if (data.event === "live_connected") {

        if (liveCallStatus) {
            liveCallStatus.textContent =
                "LIVE";
        }

        return;
    }


    if (data.event === "live_analysis") {

        const result =
            data.result || {};

        console.log(
            "LIVE ANALYSIS:",
            result
        );

        updateLiveDashboard(
            result,
            data.chunk_index
        );

        return;
    }


    if (data.event === "error") {

        console.error(
            "LIVE BACKEND ERROR:",
            data.message
        );

        if (liveCallStatus) {
            liveCallStatus.textContent =
                "ERROR";
        }

    }

}
function updateLiveDashboard(
    result,
    chunkIndex
) {

    const detection =
        result.voice_detection || {};

    const risk =
        result.risk || {};

    const prediction =
        String(
            detection.prediction || "unknown"
        ).toUpperCase();

    const fakeScore =
        Number(
            detection.fake_score || 0
        );

    const score =
        Number(
            risk.score || 0
        );

    const action =
        String(
            risk.action || "ALLOW"
        ).toUpperCase();


    if (livePrediction) {

        livePrediction.textContent =
            prediction;

    }


    if (liveFakeScore) {

        liveFakeScore.textContent =
            `${(
                fakeScore * 100
            ).toFixed(2)}%`;

    }


    if (liveRiskScore) {

        liveRiskScore.textContent =
            score.toFixed(0);

    }


    if (liveAction) {

        liveAction.textContent =
            action;

    }

    addLiveTimelineEvent(
        chunkIndex,
        prediction,
        fakeScore,
        score,
        action
    );

}

function addLiveTimelineEvent(
    chunkIndex,
    prediction,
    fakeScore,
    riskScore,
    action
) {

    if (!liveTimeline) {
        return;
    }

    const item =
        document.createElement("div");

    const isFake =
        prediction === "FAKE";

    item.className =
        isFake
            ? "live-event fake"
            : "live-event real";

    item.innerHTML = `
        <span class="live-event-index">
            ${String(
                Number(chunkIndex) + 1
            ).padStart(2, "0")}
        </span>

        <span class="live-event-state">
            ${escapeHtml(prediction)}
        </span>

        <span class="live-event-confidence">
            Fake ${(
                fakeScore * 100
            ).toFixed(1)}%
        </span>

        <span class="live-event-risk">
            Risk ${riskScore.toFixed(0)}
        </span>

        <span class="live-event-action">
            ${escapeHtml(action)}
        </span>
    `;

    liveTimeline.prepend(
        item
    );
}

function stopLiveCall(
    reason = "Stopped"
) {

    liveRunning = false;

    if (liveSocket) {

        if (
            liveSocket.readyState ===
            WebSocket.OPEN
        ) {

            liveSocket.close();

        }

        liveSocket = null;
    }

    cleanupLiveAudio();

    stopLiveTimer();

    if (liveCallStatus) {

        liveCallStatus.textContent =
            reason === "Stopped"
                ? "READY"
                : reason.toUpperCase();

    }

    updateLiveButton();
}
function cleanupLiveAudio() {

    if (liveProcessor) {

        liveProcessor.disconnect();

        liveProcessor = null;
    }

    if (liveSource) {

        liveSource.disconnect();

        liveSource = null;
    }

    if (liveAudioContext) {

        liveAudioContext.close();

        liveAudioContext = null;
    }

    stopLiveVisualizer();

    if (liveMediaStream) {

        liveMediaStream
            .getTracks()
            .forEach(
                (track) => track.stop()
            );

        liveMediaStream = null;
    }
}
function updateLiveButton() {

    if (!liveCallButton) {
        return;
    }

    if (liveRunning) {

        liveCallButton.innerHTML = `
            <span class="live-call-dot active"></span>
            STOP LIVE CALL
        `;

        liveCallButton.classList.add(
            "active"
        );

    } else {

        liveCallButton.innerHTML = `
            <span class="live-call-dot"></span>
            START LIVE CALL
        `;

        liveCallButton.classList.remove(
            "active"
        );

    }
}
if (liveCallButton) {

    liveCallButton.addEventListener(
        "click",
        async () => {

            if (liveCallActive) {

                await stopRealTimeMicrophone();

            } else {

                await startRealTimeMicrophone();

            }

        }
    );

}
function startLiveTimer() {

    stopLiveTimer();

    liveTimer =
        setInterval(
            () => {

                if (!liveStartTime) {
                    return;
                }

                const elapsed =
                    Math.floor(
                        (
                            Date.now()
                            - liveStartTime
                        ) / 1000
                    );

                const minutes =
                    String(
                        Math.floor(
                            elapsed / 60
                        )
                    ).padStart(2, "0");

                const seconds =
                    String(
                        elapsed % 60
                    ).padStart(2, "0");

                if (liveDuration) {

                    liveDuration.textContent =
                        `${minutes}:${seconds}`;

                }

            },
            1000
        );
}


function stopLiveTimer() {

    if (liveTimer) {

        clearInterval(
            liveTimer
        );

        liveTimer = null;
    }

}
/* ============================================================
   LIVE CALL SIMULATION
   Additive feature — existing analysis flow remains unchanged
============================================================ */

const simulateCallButton =
    document.getElementById("simulate-call-button");

const liveCallStatusText =
    document.getElementById("live-call-status-text");


/* ------------------------------------------------------------
   Enable live simulation when a file is selected
------------------------------------------------------------ */

function updateLiveCallButton() {

    if (!simulateCallButton) {
        return;
    }

    simulateCallButton.disabled =
        !selectedFile;

}


/* ------------------------------------------------------------
   Update live-call status
------------------------------------------------------------ */

function setLiveCallStatus(
    text,
    state = "ready"
) {

    if (!liveCallStatus) {
        return;
    }

    liveCallStatus.classList.remove(
        "hidden",
        "blocked"
    );

    if (state === "blocked") {
        liveCallStatus.classList.add("blocked");
    }

    if (liveCallStatusText) {
        liveCallStatusText.textContent =
            text;
    }

}


/* ------------------------------------------------------------
   Live call button
------------------------------------------------------------ */

if (simulateCallButton) {

    simulateCallButton.addEventListener(
        "click",
        () => {

            if (!selectedFile) {

                showFrontendError(
                    "Please select an audio file first."
                );

                return;
            }

            simulateLiveCall(
                selectedFile
            );

        }
    );

}


/* ------------------------------------------------------------
   Hook into existing file selection
------------------------------------------------------------ */


/* ------------------------------------------------------------
   LIVE CALL SIMULATION
------------------------------------------------------------ */

async function simulateLiveCall(file) {

    if (!file) {
        return;
    }

    /*
    * Reset all live-analysis state for a NEW call.
    */
    livePredictionHistory = [];
    liveAllPredictionHistory = [];

    liveStablePrediction = "unknown";
    liveStableFakeScore = 0;
    liveStableRiskScore = 0;

    liveStableNotificationSent = false;

    liveHighRiskNotificationSent = false;
    liveSuspiciousNotificationSent = false;

    liveSecurityState = "analyzing";
    liveNotificationSource = `simulation-call:${Date.now()}`;
    liveDecisionMade = false;

    setLoadingState(true);

    setLiveCallStatus(
        "CONNECTING TO VOICESHIELD...",
        "ready"
    );

    if (simulateCallButton) {
        simulateCallButton.disabled = true;
    }

    try {

        const formData =
            new FormData();

        formData.append(
            "audio",
            file
        );


        const response =
            await fetch(
                `${API_BASE}/api/simulate-call`,
                {
                    method: "POST",
                    body: formData
                }
            );


        if (!response.ok) {

            const errorText =
                await response.text();

            throw new Error(
                `Live call error ${response.status}: ${errorText}`
            );

        }


        if (!response.body) {

            throw new Error(
                "Streaming response is not supported by this browser."
            );

        }


        /*
         * Show realtime section immediately.
         */

        if (realtimeSection) {
            realtimeSection.classList.remove(
                "hidden"
            );
        }

        if (initialState) {
            initialState.classList.add(
                "hidden"
            );
        }

        if (resultState) {
            resultState.classList.remove(
                "hidden"
            );
        }


        /*
         * Read newline-delimited JSON.
         */

        const reader =
            response.body.getReader();

        const decoder =
            new TextDecoder();

        let buffer = "";


        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done) {
                break;
            }


            buffer +=
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


            const lines =
                buffer.split("\n");


            buffer =
                lines.pop() || "";


            for (const line of lines) {

                if (!line.trim()) {
                    continue;
                }


                let event;

                try {

                    event =
                        JSON.parse(line);

                } catch (parseError) {

                    console.warn(
                        "Invalid realtime event:",
                        line
                    );

                    continue;
                }


                handleLiveCallEvent(
                    event
                );

            }

        }


        /*
         * Flush any remaining decoder data.
         */

        buffer +=
            decoder.decode();


        if (buffer.trim()) {

            try {

                const event =
                    JSON.parse(
                        buffer
                    );

                handleLiveCallEvent(
                    event
                );

            } catch (error) {

                console.warn(
                    "Final realtime event could not be parsed.",
                    error
                );

            }

        }

        finalizeLiveSecurityDecision();


    } catch (error) {

        console.error(
            "Live call simulation failed:",
            error
        );

        setLiveCallStatus(
            "CONNECTION ERROR",
            "blocked"
        );

        showFrontendError(
            error.message ||
            "Unable to start live call simulation."
        );

    } finally {

        setLoadingState(false);

        if (simulateCallButton) {
            simulateCallButton.disabled =
                !selectedFile;
        }

    }

}

/* ============================================================
   REAL-TIME MICROPHONE CAPTURE
============================================================ */

async function startRealTimeMicrophone() {

    if (liveCallActive) {
        return;
    }

    try {

        if (
            !navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia
        ) {
            throw new Error(
                "Microphone access is not supported by this browser."
            );
        }

        console.log("Requesting microphone access...");

        liveMediaStream =
            await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

        if (realtimeSection) {
            realtimeSection.classList.remove("hidden");
        }

        updateLiveSecurityStatus(true);

        if (liveCallPanel) {
            liveCallPanel.classList.remove("hidden");
        }

        if (chunkTimelineCard) {
            chunkTimelineCard.classList.add("hidden");
        }

        if (chunkTimeline) {
            chunkTimeline.innerHTML = "";
        }

        if (dropZone) {
            dropZone.classList.add("hidden");
        }

        if (analyzeButton) {
            analyzeButton.classList.add("hidden");
        }

        startLiveVisualizer(liveMediaStream);

        liveChunksProcessed = 0;
        liveRiskHistory = [];
        /*
        * Reset all live-analysis state for a NEW call.
        */
        livePredictionHistory = [];
        liveAllPredictionHistory = [];

        liveStablePrediction = "unknown";
        liveStableFakeScore = 0;
        liveStableRiskScore = 0;

        liveStableNotificationSent = false;

        liveHighRiskNotificationSent = false;
        liveSuspiciousNotificationSent = false;

        liveSecurityState = "analyzing";
        liveNotificationSource = `microphone-call:${Date.now()}`;
        liveDecisionMade = false;

        /*
        * ============================================================
        * RESET SECURITY UI
        *
        * Every new call starts in a neutral/analyzing state.
        * Previous call results must not carry over.
        * ============================================================
        */

        showLiveSecurityAnalyzing();
        /*
        * Clear previous final security explanation.
        */

        const previousFinalReason =
            document.getElementById(
                "vs-live-final-reason"
            );

        if (previousFinalReason) {

            previousFinalReason.remove();

        }


        /*
        * Reset transcript.
        */

        liveTranscriptFinal = "";
        liveTranscriptInterim = "";
        liveProviderTranscript = "";
        liveTranscriptProvider = null;

        updateLiveTranscriptDisplay();
        updateLiveListeningState(true);
        updateLiveProcessingState(false);

        console.log(
            "Microphone access granted."
        );

        liveCallActive = true;
        /*
        * Keep browser speech recognition alive for the
        * duration of the live call.
        */
        liveSpeechShouldRun = true;
        /*
        * Start browser speech recognition.
        *
        * This is independent from deepfake detection.
        * If transcription fails, voice security detection
        * continues normally.
        */

        initializeLiveTranscription();

        if (
            liveSpeechRecognition &&
            liveSpeechSupported
        ) {
            try {
                liveSpeechRecognition.start();
            } catch (error) {
                console.warn(
                    "Speech recognition start warning:",
                    error
                );
            }
        }
        liveCallStartedAt = Date.now();
        liveChunkIndex = 0;
        liveDisplayedChunkCount = 0;
        updateLiveCallUI(true);

        /*
         * Start recording small chunks.
         *
         * 3 seconds is a practical starting point for
         * your current Wav2Vec2 detector.
         */

        liveMediaRecorder =
            createSupportedRecorder(
                liveMediaStream
            );

        liveMediaRecorder.ondataavailable =
            async (event) => {

                if (!event.data || event.data.size === 0) {
                    return;
                }

                console.log(
                    "Live audio chunk:",
                    event.data.size,
                    "bytes"
                );

                if (liveCallStatus) {
                    liveCallStatus.textContent =
                        `RECORDING CAPTURED • CHUNK ${liveChunkIndex + 1}`;
                }

                await processLiveChunk(
                    event.data,
                    liveChunkIndex++
                );
            };

        liveMediaRecorder.onerror =
            (event) => {

                console.error(
                    "MediaRecorder error:",
                    event
                );

                showLiveCallError(
                    "Microphone recording failed."
                );

            };

        liveMediaRecorder.start();

        if (liveCallStatus) {
            liveCallStatus.textContent = "LISTENING • FIRST CHUNK IN 3 SEC";
        }

        if (window.voiceShieldLiveMonitor) {
            await window.voiceShieldLiveMonitor.start(
                liveMediaStream
            );
        }

        startLiveCallTimer();

        /*
         * Ask MediaRecorder to produce a chunk every
         * 3 seconds.
         */

        liveChunkTimer =
            setInterval(() => {

                if (
                    liveMediaRecorder &&
                    liveMediaRecorder.state === "recording"
                ) {

                    liveMediaRecorder.stop();

                    /*
                     * A new recorder is created after each
                     * chunk so that every chunk becomes an
                     * independent audio Blob.
                     */

                    if (liveCallActive) {
                        setTimeout(() => {

                            if (liveCallActive) {
                                restartLiveRecorder();
                            }

                        }, 50);
                    }
                }

            }, 3000);

        console.log(
            "REAL-TIME MICROPHONE STARTED"
        );

    } catch (error) {

        console.error(
            "Unable to start microphone:",
            error
        );

        liveCallActive = false;

        updateLiveCallUI(false);

        if (liveCallStatus) {
            liveCallStatus.textContent =
                `ERROR: ${error.message || "LIVE ANALYSIS UNAVAILABLE"}`;
        }

        showLiveCallError(
            error.message ||
            "Microphone permission was denied."
        );
    }
}

function createSupportedRecorder(stream) {

    const mimeTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/ogg"
    ];

    for (const mimeType of mimeTypes) {

        if (
            MediaRecorder.isTypeSupported(
                mimeType
            )
        ) {

            console.log(
                "Using MediaRecorder:",
                mimeType
            );

            return new MediaRecorder(
                stream,
                {
                    mimeType
                }
            );
        }
    }

    console.log(
        "Using browser default MediaRecorder."
    );

    return new MediaRecorder(stream);
}

function restartLiveRecorder() {

    if (!liveCallActive) {
        liveProcessing = false;
        updateLiveProcessingState(false);
        return;
    }

    if (!liveMediaStream) {
        return;
    }

    liveMediaRecorder =
        createSupportedRecorder(
            liveMediaStream
        );

    liveMediaRecorder.ondataavailable =
        async (event) => {

            if (
                !event.data ||
                event.data.size === 0
            ) {
                return;
            }

            console.log(
                "Processing live chunk:",
                liveChunkIndex
            );

            await processLiveChunk(
                event.data,
                liveChunkIndex++
            );
        };

    liveMediaRecorder.onerror =
        (event) => {

            console.error(
                "Live recorder error:",
                event
            );
        };

    liveMediaRecorder.start();
}

async function processLiveChunk(
    audioBlob,
    chunkIndex
) {

    livePendingAnalyses++;
    liveProcessing = true;
    updateLiveProcessingState(true);

    if (window.voiceShieldLiveMonitor) {
        window.voiceShieldLiveMonitor.processing(
            chunkIndex
        );
    }

    const extension =
        audioBlob.type.includes("ogg")
            ? "ogg"
            : "webm";

    const chunkFile =
        new File(
            [audioBlob],
            `live_chunk_${chunkIndex}.${extension}`,
            {
                type: audioBlob.type ||
                    "audio/webm"
            }
        );

    const formData =
        new FormData();

    /*
     * IMPORTANT:
     *
     * Your FastAPI endpoint expects:
     *
     * audio: UploadFile
     *
     */

    formData.append(
        "audio",
        chunkFile
    );

    console.log(
        `Sending live chunk ${chunkIndex} to backend...`
    );

    const processingStatus =
        document.getElementById(
            "live-processing-status"
        );

    if (processingStatus) {
        processingStatus.textContent =
            `Listening - analyzing chunk ${chunkIndex + 1}`;
    }

    if (liveCallStatus) {
        liveCallStatus.textContent =
            `SENDING RECORDING • CHUNK ${chunkIndex + 1}`;
    }

    try {

        const response =
            await fetch(
                `${API_BASE}/api/simulate-call`,
                {
                    method: "POST",
                    body: formData
                }
            );

        if (!response.ok) {

            const errorText =
                await response.text();

            throw new Error(
                `Live analysis failed (${response.status}): ${errorText}`
            );
        }

        const data =
            await response.json();

        appendProviderTranscript(
            data.transcription
        );

        console.log(
            "LIVE BACKEND RESULT:",
            data
        );

        if (!data.events || !Array.isArray(data.events)) {
            throw new Error(
                "Backend returned no live analysis events."
            );
        }

        if (data.events.length === 0) {
            throw new Error(
                "Recording chunk contained no analyzable audio."
            );
        }

        if (liveCallStatus) {
            liveCallStatus.textContent =
                `ANALYSIS RECEIVED • CHUNK ${chunkIndex + 1}`;
        }

        if (
            data.events &&
            Array.isArray(data.events)
        ) {

            data.events.forEach((event) =>
                handleLiveAnalysisEvent({
                    ...event,
                    live_chunk_index: chunkIndex
                })
            );
        }

        liveChunksProcessed++;

    } catch (error) {

        console.error(
            "Live chunk analysis error:",
            error
        );

        showLiveCallError(
            error.message
        );

        if (liveCallStatus) {
            liveCallStatus.textContent =
                `ANALYSIS ERROR: ${error.message}`;
        }

    } finally {
        livePendingAnalyses = Math.max(
            livePendingAnalyses - 1,
            0
        );
        liveProcessing = livePendingAnalyses > 0;

        if (liveProcessing || liveCallActive) {
            updateLiveProcessingState(liveProcessing);
        } else if (
            livePendingAnalyses === 0 &&
            !liveDecisionMade
        ) {
            finalizeLiveSecurityDecision();
        }
    }
}
function handleLiveAnalysisEvent(event) {

    console.log(
        "LIVE EVENT:",
        event
    );

    if (
        event.event ===
        "chunk_analysis"
    ) {

        const processingStatus =
            document.getElementById(
                "live-processing-status"
            );

        if (processingStatus) {
            processingStatus.textContent =
                `Live analysis complete - chunk ${Number(event.live_chunk_index || 0) + 1}`;
        }

        renderLiveChunkResult(
            event
        );

        if (window.voiceShieldLiveMonitor) {
            window.voiceShieldLiveMonitor.analyzed(
                event.live_chunk_index
            );
        }

        return;
    }

    if (
        event.event ===
        "call_complete"
    ) {

        console.log(
            "Live chunk completed:",
            event
        );

    }
}

function finalizeLiveSecurityDecision() {

    if (
        liveAllPredictionHistory.length === 0
    ) {
        console.warn(
            "Cannot finalize live security decision: no processed chunks."
        );

        return;
    }

    const completionLabel =
        String(liveNotificationSource || "").startsWith("simulation-call:")
            ? "TEST COMPLETED"
            : "CALL COMPLETED";

    if (liveDecisionMade) {
        showLiveCompletionSummary(
            liveStablePrediction,
            {
                stable: true,
                prediction: liveStablePrediction,
                fakeScore: liveStableFakeScore,
                riskScore: liveStableRiskScore,
                evidenceCount: livePredictionHistory.length,
                requiredCount: LIVE_STABLE_REQUIRED
            },
            completionLabel
        );
        return;
    }

    /*
    * ============================================================
    * FINAL ALL-CHUNK AGGREGATION
    * ============================================================
    */

    const fakeCount =
        observations.filter(
            item =>
                item.prediction === "fake"
        ).length;

    const realCount =
        observations.filter(
            item =>
                item.prediction === "real"
        ).length;

    const unknownCount =
        observations.filter(
            item =>
                item.prediction !== "fake" &&
                item.prediction !== "real"
        ).length;

    const totalCount =
        observations.length;

    const fakePercentage =
        totalCount > 0
            ? (fakeCount / totalCount) * 100
            : 0;

    const realPercentage =
        totalCount > 0
            ? (realCount / totalCount) * 100
            : 0;

    const averageFakeScore =
        observations.reduce(
            (sum, item) =>
                sum + Number(item.fakeScore || 0),
            0
        ) / totalCount;

    const averageRiskScore =
        observations.reduce(
            (sum, item) =>
                sum + Number(item.riskScore || 0),
            0
        ) / totalCount;

    /*
    * ============================================================
    * FINAL DECISION
    * ============================================================
    *
    * FAKE wins when it has more evidence than REAL.
    *
    * REAL wins only when REAL has more evidence.
    *
    * A tie becomes SUSPICIOUS.
    */
    let prediction = "suspicious";

    if (
        fakeCount > realCount
    ) {
        prediction = "fake";
    } else if (
        realCount > fakeCount
    ) {
        prediction = "real";
    }

    /*
    * If more than half of the observations are unknown,
    * the final result is not reliable enough to call REAL/FAKE.
    */
    if (
        unknownCount >
        totalCount / 2
    ) {
        prediction = "suspicious";
    }

    const finalRiskScore =
        prediction === "fake"
            ? Math.max(
                averageRiskScore,
                averageFakeScore * 100,
                fakePercentage
            )
            : prediction === "suspicious"
                ? Math.max(
                    averageRiskScore,
                    fakePercentage
                )
                : Math.min(
                    averageRiskScore,
                    fakePercentage
                );

    const stableResult = {
        stable: true,

        prediction,

        fakeScore:
            averageFakeScore,

        riskScore:
            Math.min(
                100,
                finalRiskScore
            ),

        /*
        * FINAL evidence count.
        */
        evidenceCount:
            totalCount,

        requiredCount:
            totalCount,

        fakeCount,
        realCount,
        unknownCount,

        fakePercentage,
        realPercentage
    };

    updateLiveThreatDisplay(
        {
            prediction,
            fake_score: averageFakeScore,
            risk_score: stableResult.riskScore,
            stable: true
        },
        stableResult
    );

    showLiveCompletionSummary(
        prediction,
        stableResult,
        completionLabel
    );
    /*
    * Add the actual evidence count to the existing
    * live evidence display.
    *
    * No frontend HTML structure change is required.
    */
    updateLiveEvidenceDisplay(
        stableResult
    );

    if (liveCallStatus) {
        liveCallStatus.textContent = "CALL ANALYSIS COMPLETE";
    }
    liveDecisionMade = true;
}
function showLiveCompletionSummary(
    prediction,
    stableResult,
    label = "TEST COMPLETED"
) {
    const normalizedPrediction =
        String(prediction || "unknown").toLowerCase();

    const isFake = normalizedPrediction === "fake";
    const isReal = normalizedPrediction === "real";
    const isSuspicious =
        !isFake && !isReal;

    /*
     * ------------------------------------------------------------
     * FINAL VERDICT
     * ------------------------------------------------------------
     */

    const verdict = isFake
        ? "FAKE"
        : isReal
        ? "REAL"
        : "SUSPICIOUS";

    /*
     * ------------------------------------------------------------
     * FINAL STATUS HEADER
     * ------------------------------------------------------------
     */

    const badge = isFake
        ? "[⚠ COMPLETED] SYNTHETIC VOICE DETECTED"
        : isReal
        ? "[✓ COMPLETED] AUTHENTIC VOICE VERIFIED"
        : "[⚡ COMPLETED] INCONCLUSIVE / SUSPICIOUS PATTERN";

    /*
     * ------------------------------------------------------------
     * FINAL TITLE
     * ------------------------------------------------------------
     */

    const title = isFake
        ? "Synthetic Voice Detected"
        : isReal
        ? "Authentic Voice Confirmed"
        : "Suspicious Audio Detected";

    /*
     * ------------------------------------------------------------
     * FINAL DESCRIPTION + RECOMMENDED ACTION
     * ------------------------------------------------------------
     */

    const description = isFake
        ? "Multiple voice segments generated strong deepfake evidence. Recommended Action: Block call immediately."
        : isReal
        ? "Voice traits match expected human baseline. It is safe to proceed with this call."
        : "Inconsistent audio signals detected. Exercise caution before proceeding.";

    const action = isFake
        ? "BLOCK"
        : isReal
        ? "ALLOW"
        : "MONITOR";

    /*
     * ------------------------------------------------------------
     * REMOVE TEMPORARY ANALYZING STATE
     * ------------------------------------------------------------
     */

    const processingStatus =
        document.getElementById("live-processing-status");

    if (processingStatus) {
        processingStatus.textContent =
            "TEST COMPLETED";

        processingStatus.classList.remove("processing");
    }

    /*
     * ------------------------------------------------------------
     * SECURITY STATUS HEADER
     * ------------------------------------------------------------
     */

    if (resultTag) {
        resultTag.textContent =
            "TEST COMPLETED";
    }

    /*
     * ------------------------------------------------------------
     * APPLY FINAL SECURITY COLOUR
     * ONLY AFTER ALL ANALYSIS IS COMPLETE
     * ------------------------------------------------------------
     */

    document.body.classList.remove(
        "security-danger",
        "security-success",
        "security-warning"
    );

    document.body.classList.add(
        isFake
            ? "security-danger"
            : isReal
            ? "security-success"
            : "security-warning"
    );

    /*
     * ------------------------------------------------------------
     * FINAL RESULT BADGE
     * ------------------------------------------------------------
     */

    if (predictionBadge) {
        predictionBadge.className = "prediction-badge";
        predictionBadge.textContent = badge;
    }

    /*
     * ------------------------------------------------------------
     * FINAL RESULT TITLE
     * ------------------------------------------------------------
     */

    if (predictionText) {
        predictionText.textContent = title;
    }

    /*
     * ------------------------------------------------------------
     * FINAL RESULT DESCRIPTION
     * ------------------------------------------------------------
     */

    if (predictionDescription) {
        predictionDescription.textContent = description;
    }

    /*
     * ------------------------------------------------------------
     * FINAL RISK STATE
     * ------------------------------------------------------------
     */

    if (riskLevel) {
        riskLevel.textContent =
            isFake
                ? "HIGH RISK"
                : isReal
                ? "LOW RISK"
                : "MEDIUM RISK";
    }

    if (riskAction) {
        riskAction.textContent = action;
    }

    /*
     * ------------------------------------------------------------
     * FINAL RISK STYLING
     * ------------------------------------------------------------
     */

    applyRiskStyle(
        isFake
            ? "HIGH"
            : isReal
            ? "LOW"
            : "MEDIUM"
    );

    /*
     * ------------------------------------------------------------
     * FINAL EVIDENCE / COMPLETION INDICATOR
     * ------------------------------------------------------------
     */

    updateLiveEvidenceDisplay({
        ...(stableResult || {}),
        stable: true,
        prediction: normalizedPrediction,
        completionLabel: "TEST COMPLETED"
    });

    /*
     * ------------------------------------------------------------
     * OPTIONAL ADDITIONAL VERIFICATION
     * ------------------------------------------------------------
     * Only suspicious/inconclusive calls should expose the
     * challenge-response panel.
     */
    if (isSuspicious) {
        window.dispatchEvent(
            new CustomEvent("voiceshield:challenge-show", {
                detail: {
                    riskScore: Number(stableResult?.riskScore || 0),
                    prediction: normalizedPrediction
                }
            })
        );
    }

    /*
     * ------------------------------------------------------------
     * LOG FINAL SECURITY DECISION
     * ------------------------------------------------------------
     */

    console.log(
        `LIVE ANALYSIS COMPLETED: ${verdict}`
    );

    console.log(
        "FINAL LIVE SECURITY RESULT:",
        {
            verdict,
            action,
            evidenceCount:
                stableResult?.evidenceCount || 0,
            requiredCount:
                stableResult?.requiredCount ||
                LIVE_STABLE_REQUIRED
        }
    );
}
/* ============================================================
   LIVE PREDICTION STABILITY
============================================================ */

/* ============================================================
   FINAL LIVE DECISION ENGINE
   ------------------------------------------------------------
   Individual chunks NEVER change the final security state.

   Four consecutive strong results are required.
   ============================================================ */

function calculateStableLiveResult(event) {
    /*
     * ============================================================
     * REAL-TIME STABILITY + ACCUMULATED EVIDENCE
     * ============================================================
     *
     * This function serves TWO purposes:
     *
     * 1. Keep the latest 4 chunks for immediate live decisions.
     * 2. Keep ALL processed chunks for the final call decision.
     *
     * The rolling window is never used as the final call history.
     */

    const prediction = String(
        event?.prediction || "unknown"
    ).toLowerCase();

    const fakeScore = Number(
        event?.fake_score ?? 0
    );

    const riskScore = Number(
        event?.risk_score ?? 0
    );

    /*
     * ------------------------------------------------------------
     * VALIDATE NUMERIC VALUES
     * ------------------------------------------------------------
     *
     * Never allow NaN / Infinity to corrupt the risk calculation.
     */
    const safeFakeScore =
        Number.isFinite(fakeScore)
            ? Math.max(0, Math.min(1, fakeScore))
            : 0;

    const safeRiskScore =
        Number.isFinite(riskScore)
            ? Math.max(0, Math.min(100, riskScore))
            : 0;

    /*
     * ------------------------------------------------------------
     * STORE IN ALL-CHUNK HISTORY
     * ------------------------------------------------------------
     *
     * This array is NEVER shifted.
     */
    liveAllPredictionHistory.push({
        prediction,
        fakeScore: safeFakeScore,
        riskScore: safeRiskScore,
        timestamp: Date.now()
    });

    /*
     * ------------------------------------------------------------
     * STORE IN ROLLING 4-CHUNK WINDOW
     * ------------------------------------------------------------
     */
    livePredictionHistory.push({
        prediction,
        fakeScore: safeFakeScore,
        riskScore: safeRiskScore,
        timestamp: Date.now()
    });

    /*
     * Keep ONLY the latest 4 chunks here.
     */
    if (
        livePredictionHistory.length >
        LIVE_STABILITY_WINDOW
    ) {
        livePredictionHistory.shift();
    }

    /*
     * ------------------------------------------------------------
     * NOT ENOUGH DATA FOR A STABLE LIVE DECISION
     * ------------------------------------------------------------
     */
    if (
        livePredictionHistory.length <
        LIVE_STABILITY_WINDOW
    ) {
        liveSecurityState = "analyzing";

        return {
            stable: false,
            prediction: "verifying",

            fakeScore: safeFakeScore,
            riskScore: safeRiskScore,

            evidenceCount:
                livePredictionHistory.length,

            requiredCount:
                LIVE_STABILITY_WINDOW,

            totalEvidenceCount:
                liveAllPredictionHistory.length
        };
    }

    const recent = livePredictionHistory;

    /*
     * ------------------------------------------------------------
     * ROLLING-WINDOW COUNTS
     * ------------------------------------------------------------
     */

    const strongFakeCount =
        recent.filter(item =>
            item.prediction === "fake" &&
            item.fakeScore >= LIVE_FAKE_THRESHOLD
        ).length;

    const realCount =
        recent.filter(item =>
            item.prediction === "real"
        ).length;

    const fakeCount =
        recent.filter(item =>
            item.prediction === "fake"
        ).length;

    const suspiciousCount =
        recent.filter(item =>
            item.prediction !== "fake" &&
            item.prediction !== "real"
        ).length;

    /*
     * Average values from the latest 4 chunks.
     */
    const averageFakeScore =
        recent.reduce(
            (sum, item) =>
                sum + item.fakeScore,
            0
        ) / recent.length;

    const averageRiskScore =
        recent.reduce(
            (sum, item) =>
                sum + item.riskScore,
            0
        ) / recent.length;

    /*
     * ------------------------------------------------------------
     * LIVE SECURITY STATE
     * ------------------------------------------------------------
     *
     * We intentionally require 3 of the latest 4 chunks to
     * support a strong live conclusion.
     *
     * This prevents ONE bad/noisy chunk from triggering an alarm.
     */
    let livePrediction = "suspicious";

    /*
     * HIGH-RISK FAKE
     *
     * At least 3 of the latest 4 chunks must be:
     *
     * prediction = fake
     * AND
     * fakeScore >= 0.85
     */
    if (
        strongFakeCount >= 3
    ) {
        livePrediction = "fake";
    }

    /*
     * AUTHENTIC / REAL
     *
     * At least 3 of the latest 4 chunks must be REAL.
     *
     * Notice that REAL does NOT win merely because the average
     * fake score happens to be low.
     */
    else if (
        realCount >= 3 &&
        strongFakeCount === 0
    ) {
        livePrediction = "real";
    }

    /*
     * Otherwise the current rolling evidence is inconclusive.
     */
    else {
        livePrediction = "suspicious";
    }

    /*
     * ------------------------------------------------------------
     * LIVE STATE
     * ------------------------------------------------------------
     */
    liveSecurityState =
        livePrediction;

    /*
     * ------------------------------------------------------------
     * LIVE RISK SCORE
     * ------------------------------------------------------------
     *
     * If 3/4 or 4/4 are strong FAKE, risk must be high.
     */
    let liveRiskScore =
        averageRiskScore;

    if (
        livePrediction === "fake"
    ) {
        liveRiskScore = Math.max(
            averageRiskScore,
            averageFakeScore * 100,
            (strongFakeCount / recent.length) * 100
        );
    }

    /*
     * Suspicious should never accidentally become "safe".
     */
    if (
        livePrediction === "suspicious"
    ) {
        liveRiskScore = Math.max(
            liveRiskScore,
            (strongFakeCount / recent.length) * 100
        );
    }

    /*
     * ------------------------------------------------------------
     * RETURN LIVE RESULT
     * ------------------------------------------------------------
     */
    return {
        stable: true,

        prediction:
            livePrediction,

        fakeScore:
            averageFakeScore,

        riskScore:
            Math.min(100, liveRiskScore),

        evidenceCount:
            recent.length,

        requiredCount:
            LIVE_STABILITY_WINDOW,

        totalEvidenceCount:
            liveAllPredictionHistory.length,

        fakeCount,

        strongFakeCount,

        realCount,

        suspiciousCount
    };
}
/*
 * ============================================================
 * REAL-TIME SECURITY NOTIFICATION
 * ============================================================
 *
 * This function is intentionally separate from the FINAL
 * completion notification.
 *
 * It warns the user while the call is still happening.
 */
async function handleLiveSecurityState(
    stableResult
) {
    if (
        !stableResult ||
        !stableResult.stable
    ) {
        return;
    }

    const prediction =
        String(
            stableResult.prediction || ""
        ).toLowerCase();

    /*
     * ------------------------------------------------------------
     * HIGH RISK / FAKE
     * ------------------------------------------------------------
     */
    if (
        prediction === "fake"
    ) {
        /*
         * Update the visible live UI immediately.
         *
         * This uses the EXISTING UI functions.
         * No HTML structure changes are required.
         */
        updateLiveThreatDisplay({
            prediction: "fake",
            fake_score:
                stableResult.fakeScore,
            risk_score:
                stableResult.riskScore,
            stable: true
        });

        /*
         * Send ONLY ONE high-risk notification per call.
         *
         * Do not spam the user for every subsequent chunk.
         */
        if (
            !liveHighRiskNotificationSent &&
            liveNotificationSource
        ) {
            liveHighRiskNotificationSent = true;

            try {
                await publishStableLiveNotification(
                    stableResult,
                    "HIGH",
                    "BLOCK"
                );
            } catch (error) {
                /*
                 * Notification failure must NEVER stop
                 * the voice-analysis pipeline.
                 */
                liveHighRiskNotificationSent = false;

                console.warn(
                    "Real-time high-risk notification failed:",
                    error
                );
            }
        }

        return;
    }

    /*
     * ------------------------------------------------------------
     * SUSPICIOUS
     * ------------------------------------------------------------
     */
    if (
        prediction === "suspicious"
    ) {
        /*
         * Keep the UI cautious.
         *
         * We do NOT mark the call as REAL.
         */
        if (predictionBadge) {
            predictionBadge.textContent =
                "⚡ SUSPICIOUS AUDIO";
        }

        if (predictionText) {
            predictionText.textContent =
                "Suspicious audio detected";
        }

        if (predictionDescription) {
            predictionDescription.textContent =
                "Inconsistent voice signals detected. VoiceShield is continuing to collect evidence.";
        }

        if (riskLevel) {
            riskLevel.textContent =
                "SUSPICIOUS";
        }

        if (riskAction) {
            riskAction.textContent =
                "EXERCISE CAUTION";
        }

        /*
         * Do NOT turn the application red for merely
         * suspicious evidence.
         */
        document.body.classList.remove(
            "security-danger"
        );

        /*
         * A suspicious notification is optional.
         *
         * We send it only once if the existing notification
         * pipeline is available.
         */
        if (
            !liveSuspiciousNotificationSent &&
            liveNotificationSource
        ) {
            liveSuspiciousNotificationSent = true;

            try {
                await publishStableLiveNotification(
                    stableResult,
                    "MEDIUM",
                    "CAUTION"
                );
            } catch (error) {
                liveSuspiciousNotificationSent = false;

                console.warn(
                    "Suspicious live notification failed:",
                    error
                );
            }
        }

        return;
    }

    /*
     * ------------------------------------------------------------
     * REAL
     * ------------------------------------------------------------
     *
     * Do NOT send a "safe" notification.
     *
     * Real-time REAL means:
     *
     * "No strong synthetic evidence in the latest window."
     *
     * It should not be interpreted as proof of identity.
     */
    if (
        prediction === "real"
    ) {
        updateLiveThreatDisplay({
            prediction: "real",
            fake_score:
                stableResult.fakeScore,
            risk_score:
                stableResult.riskScore,
            stable: true
        });
    }
}
function renderLiveChunkResult(event) {
    /*
     * Frontend-owned chunk number.
     *
     * The backend analyzes each uploaded microphone
     * chunk as an independent request and therefore
     * may return chunk_index = 0 every time.
     *
     * We keep the real live-call sequence here.
     */
    liveDisplayedChunkCount++;

    const displayChunkIndex =
        Number.isFinite(Number(event.live_chunk_index))
            ? Number(event.live_chunk_index)
            : liveDisplayedChunkCount - 1;

    /*
     * Reuse the existing realtime timeline.
     */
    if (chunkTimeline) {

        if (chunkTimelineCard) {
            chunkTimelineCard.classList.remove("hidden");
        }

        const element = document.createElement("div");

        const fake = String(event.prediction || "").toLowerCase() === "fake";

        element.className = fake ? "chunk fake" : "chunk";

        element.innerHTML = `
            <div class="chunk-index">
                LIVE ${String(displayChunkIndex + 1).padStart(2, "0")}
            </div>

            <div class="chunk-prediction">
                ${String(event.prediction || "UNKNOWN").toUpperCase()}
            </div>

            <div class="chunk-score">
                ${(Number(event.confidence || 0) * 100).toFixed(2)}% confidence
            </div>
        `;

        chunkTimeline.appendChild(element);
    }

    /*
     * ------------------------------------------------------------
     * STABILIZE LIVE RESULT BEFORE UPDATING
     * THE MAIN SECURITY DECISION.
     * ------------------------------------------------------------
     */
    const stableResult = calculateStableLiveResult(event);
    /*
    * Process the current rolling 4-chunk security state.
    *
    * This runs DURING the call.
    */
    if (
        stableResult &&
        stableResult.stable === true
    ) {
        handleLiveSecurityState(
            stableResult
        ).catch(error => {
            /*
            * A notification/UI failure must never
            * terminate audio analysis.
            */
            console.warn(
                "Live security-state handler failed:",
                error
            );
        });
    }
    /*
     * ============================================================
     * FINAL STABLE SECURITY DECISION
     *
     * IMPORTANT:
     * Do NOT change the UI colour based on individual chunks.
     * The colour changes only after the stable result is confirmed.
     * ============================================================
     */
    if (stableResult && stableResult.stable === true) {

        if (String(stableResult.prediction).toLowerCase() === "fake") {

            /*
             * ============================================================
             * FINAL FAKE CONCLUSION
             * ============================================================
             */
            if (predictionBadge) {
                predictionBadge.textContent = "⚠ FAKE VOICE DETECTED";
            }

            if (predictionText) {
                predictionText.textContent = "Synthetic voice detected";
            }

            if (predictionDescription) {
                predictionDescription.textContent =
                    "Multiple consecutive voice segments produced strong synthetic-voice evidence. The call should be blocked.";
            }

            if (riskLevel) {
                riskLevel.textContent = "HIGH RISK";
            }

            if (riskAction) {
                riskAction.textContent = "BLOCK";
            }

            document.body.classList.add("security-danger");

        } else if (String(stableResult.prediction).toLowerCase() === "real") {

            /*
             * ============================================================
             * FINAL REAL CONCLUSION
             * ============================================================
             */
            if (predictionBadge) {
                predictionBadge.textContent = "✓ REAL VOICE VERIFIED";
            }

            if (predictionText) {
                predictionText.textContent = "Authentic voice detected";
            }

            if (predictionDescription) {
                predictionDescription.textContent =
                    "Multiple consecutive voice segments remained consistent with an authentic voice. The call can be allowed.";
            }

            if (riskLevel) {
                riskLevel.textContent = "LOW RISK";
            }

            if (riskAction) {
                riskAction.textContent = "ALLOW";
            }

            document.body.classList.remove("security-danger");
        }

    } else {

        /*
         * ========================================================
         * STILL VERIFYING
         *
         * Individual chunks are NOT allowed to turn the
         * interface red or green.
         * ========================================================
         */
        document.body.classList.remove("security-danger");

        if (riskAction) {
            riskAction.textContent = "MONITOR";
        }

        if (riskLevel) {
            riskLevel.textContent = "ANALYZING";
        }
    }

    /*
     * Always show the individual chunk
     * in the timeline.
     */
    updateLiveDashboard(
        {
            voice_detection: {
                prediction: event.prediction,
                fake_score: event.fake_score
            },
            risk: {
                score: event.risk_score,
                action: event.action,
                level: event.risk_level
            }
        },
        event.live_chunk_index
    );

    /*
     * Main dashboard only changes after
     * enough evidence has accumulated.
     */
    updateLiveThreatDisplay({
        ...event,
        prediction: stableResult ? stableResult.prediction : event.prediction,
        fake_score: stableResult ? stableResult.fakeScore : event.fake_score,
        risk_score: stableResult ? stableResult.riskScore : event.risk_score,
        stable: stableResult ? stableResult.stable : false
    }, stableResult);
}

function updateLiveThreatDisplay(event, stableResult) {

    const rawPrediction =
        String(
            event.prediction || "unknown"
        ).toLowerCase();

    const rawFakeScore =
        Number(
            event.fake_score || 0
        );

    const rawRiskScore =
        Number(
            event.risk_score || 0
        );


    /*
     * ========================================================
     * CALCULATE FINAL STABLE RESULT
     * ========================================================
     */

    /*
     * Keep risk history for the small trend indicator.
     *
     * This does NOT control the global security colour.
     */

    recordLiveRisk(
        rawRiskScore
    );


    /* ========================================================
       VERIFYING
       ======================================================== */

    if (!stableResult.stable) {

        /*
         * VERY IMPORTANT:
         * Do not show FAKE as the final result yet.
         */

        if (voiceResult) {

            voiceResult.textContent =
                "VERIFYING";

        }

        if (fakeScore) {

            fakeScore.textContent =
                `${(
                    rawFakeScore * 100
                ).toFixed(2)}%`;

        }

        if (fakeScoreBar) {

            fakeScoreBar.style.width =
                `${Math.min(
                    rawFakeScore * 100,
                    100
                )}%`;

        }


        /*
         * Keep entire application neutral.
         */

        document.body.classList.remove(
            "security-danger"
        );


        if (predictionBadge) {
            predictionBadge.innerHTML = `
                <div class="live-analysis-loader">
                    <div class="matrix-loader" aria-hidden="true"></div>
                    <div class="live-analysis-label">ANALYZING VOICE</div>
                </div>
            `;

            predictionBadge.className =
                "prediction-badge live live-analyzing";
        }


        if (predictionText) {

            predictionText.textContent =
                "Analyzing voice consistency";

        }


        if (predictionDescription) {

            predictionDescription.textContent =
                `VoiceShield is comparing consecutive voice segments. ` +
                `${stableResult.evidenceCount}/` +
                `${stableResult.requiredCount} ` +
                `stable observations collected.`;

        }


        if (riskLevel) {

            riskLevel.textContent =
                "VERIFYING";

        }


        if (riskAction) {

            riskAction.textContent =
                "MONITOR";

        }


        /*
         * Show the evidence counter in the live monitor.
         */

        updateLiveEvidenceDisplay(
            stableResult
        );

        return;

    }


    /* ========================================================
       STABLE FINAL RESULT
       ======================================================== */

    const finalPrediction =
        stableResult.prediction;

    const finalFakeScore =
        stableResult.fakeScore;

    const finalRiskScore =
        stableResult.riskScore;


    /*
     * ========================================================
     * STABLE FAKE
     * ========================================================
     */

    if (
        finalPrediction === "fake"
    ) {

        /*
         * NOW — and only now — turn the application red.
         */

        document.body.classList.add(
            "security-danger"
        );


        if (voiceResult) {

            voiceResult.textContent =
                "FAKE — CONFIRMED";

        }


        if (fakeScore) {

            fakeScore.textContent =
                `${(
                    finalFakeScore * 100
                ).toFixed(2)}%`;

        }


        if (fakeScoreBar) {

            fakeScoreBar.style.width =
                `${Math.min(
                    finalFakeScore * 100,
                    100
                )}%`;

        }


        if (predictionBadge) {

            predictionBadge.className =
                "prediction-badge";

            predictionBadge.textContent =
                "SYNTHETIC VOICE CONFIRMED";

            predictionBadge.style.color =
                "var(--danger)";

            predictionBadge.style.borderColor =
                "rgba(255,84,112,0.35)";

            predictionBadge.style.background =
                "var(--danger-soft)";

        }


        if (predictionText) {

            predictionText.textContent =
                "Stable AI-generated voice detected";

        }


        if (predictionDescription) {

            predictionDescription.textContent =
                `HIGH RISK — ${(
                    finalFakeScore * 100
                ).toFixed(1)}% average synthetic-voice probability ` +
                `across ${LIVE_STABLE_REQUIRED} consecutive observations. ` +
                `VoiceShield recommends BLOCK.`;

        }


        if (riskScore) {

            riskScore.textContent =
                Math.round(
                    finalRiskScore
                );

        }


        if (riskLevel) {

            riskLevel.textContent =
                "HIGH RISK";

        }


        if (riskAction) {

            riskAction.textContent =
                "BLOCK";

        }


        /*
         * Apply final risk styling ONLY here.
         */

        applyRiskStyle(
            "HIGH"
        );

        if (resultTag) {
            resultTag.textContent = "LIVE • FINAL";
        }
        /*
        * IMPORTANT:
        * This is a LIVE security state, not the final
        * call-level decision.
        *
        * Do NOT set:
        * liveDecisionMade = true;
        */
        publishStableLiveNotification(
            stableResult,
            "HIGH",
            "BLOCK"
        );


        updateLiveFinalReason(
            "UNSAFE",
            [
                "Multiple consecutive voice segments were classified as synthetic.",
                `Average fake probability: ${(
                    finalFakeScore * 100
                ).toFixed(1)}%.`,
                `The result remained consistent across ${LIVE_STABLE_REQUIRED} observations.`,
                "Recommended action: BLOCK the call."
            ]
        );


        updateLiveEvidenceDisplay(
            stableResult
        );

        return;

    }


    /*
     * ========================================================
     * STABLE REAL
     * ========================================================
     */

    if (
        finalPrediction === "real"
    ) {

        /*
         * Explicitly make sure the previous danger state
         * is removed only after a STABLE REAL decision.
         */

        document.body.classList.remove(
            "security-danger"
        );


        if (voiceResult) {

            voiceResult.textContent =
                "REAL — VERIFIED";

        }


        if (fakeScore) {

            fakeScore.textContent =
                `${(
                    finalFakeScore * 100
                ).toFixed(2)}%`;

        }


        if (fakeScoreBar) {

            fakeScoreBar.style.width =
                `${Math.min(
                    finalFakeScore * 100,
                    100
                )}%`;

        }


        if (predictionBadge) {

            predictionBadge.className =
                "prediction-badge";

            predictionBadge.textContent =
                "VOICE VERIFIED";

            predictionBadge.style.color =
                "var(--neon)";

            predictionBadge.style.borderColor =
                "var(--border-bright)";

            predictionBadge.style.background =
                "var(--neon-soft)";

        }


        if (predictionText) {

            predictionText.textContent =
                "Authentic voice detected";

        }


        if (predictionDescription) {

            predictionDescription.textContent =
                `LOW RISK — voice remained consistent across ` +
                `${LIVE_STABLE_REQUIRED} consecutive observations.`;

        }


        if (riskScore) {

            riskScore.textContent =
                Math.round(
                    finalRiskScore
                );

        }


        if (riskLevel) {

            riskLevel.textContent =
                "LOW RISK";

        }


        if (riskAction) {

            riskAction.textContent =
                "ALLOW";

        }


        /*
         * Apply GREEN/SAFE styling only after
         * stable REAL is confirmed.
         */

        applyRiskStyle(
            "LOW"
        );

        if (resultTag) {
            resultTag.textContent = "LIVE • FINAL";
        }


        publishStableLiveNotification(
            stableResult,
            "LOW",
            "ALLOW"
        );


        updateLiveFinalReason(
            "SAFE",
            [
                "No persistent synthetic-voice pattern was detected.",
                `Average fake probability: ${(
                    finalFakeScore * 100
                ).toFixed(1)}%.`,
                `The voice remained consistent across ${LIVE_STABLE_REQUIRED} observations.`,
                "Recommended action: ALLOW the call."
            ]
        );


        updateLiveEvidenceDisplay(
            stableResult
        );

    }

}

async function publishStableLiveNotification(
    stableResult,
    riskLevel,
    action
) {
    if (liveStableNotificationSent || !liveNotificationSource) {
        return;
    }

    liveStableNotificationSent = true;

    try {
        const response = await fetch(`${API_BASE}/api/notifications/live-final`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                source: liveNotificationSource,
                risk_score: stableResult.riskScore,
                risk_level: riskLevel,
                action,
                reasons: [
                    `Stable ${stableResult.prediction.toUpperCase()} voice decision from ${LIVE_STABLE_REQUIRED} consecutive observations.`
                ]
            })
        });

        if (!response.ok) {
            throw new Error(`Stable notification failed (${response.status})`);
        }
        const data = await response.json();
        if (data.notification && window.voiceShieldNotify) {
            await window.voiceShieldNotify(data.notification);
        }
    } catch (error) {
        liveStableNotificationSent = false;
        console.warn("Stable live notification failed:", error);
    }
}
/* ============================================================
   LIVE EVIDENCE COUNTER
   ============================================================ */

function updateLiveEvidenceDisplay(
    stableResult
) {

    const monitor =
        document.querySelector(
            ".vs-live-monitor"
        );

    if (!monitor) {
        return;
    }

    let evidence =
        document.getElementById(
            "vs-live-evidence"
        );

    /*
     * Create it once.
     * This does NOT require changing index.html.
     */

    if (!evidence) {

        evidence =
            document.createElement(
                "div"
            );

        evidence.id =
            "vs-live-evidence";

        evidence.style.marginTop =
            "8px";

        evidence.style.textAlign =
            "center";

        evidence.style.fontSize =
            "10px";

        evidence.style.letterSpacing =
            "0.08em";

        evidence.style.opacity =
            "0.65";

        monitor.appendChild(
            evidence
        );

    }

    if (
        stableResult.stable
    ) {
        const processedChunks =
            Number(stableResult.evidenceCount || 0);

        const totalChunks =
            Number(
                stableResult.requiredCount ||
                LIVE_STABLE_REQUIRED ||
                processedChunks
            );

        evidence.textContent =
            `STATUS: ${stableResult.completionLabel || "TEST COMPLETED"} • ` +
            `${processedChunks}/${totalChunks} CHUNKS PROCESSED`;
    }else {

        evidence.textContent =
            `SECURITY VERIFICATION • ` +
            `${stableResult.evidenceCount}/` +
            `${stableResult.requiredCount} OBSERVATIONS`;

    }

}

function riskScoreElementExists() {

    return Boolean(
        document.getElementById(
            "risk-score"
        )
    );
}
async function stopRealTimeMicrophone() {

    console.log(
        "Stopping live microphone..."
    );

    liveCallActive = false;
    /*
    * Stop browser transcription.
    */

    if (
        liveSpeechRecognition
    ) {

        if (liveTranscriptInterim.trim()) {
            liveTranscriptFinal +=
                `${liveTranscriptInterim.trim()} `;
            liveTranscriptInterim = "";
            updateLiveTranscriptDisplay();
        }

        try {

            liveSpeechRecognition.stop();

        } catch (error) {

            console.warn(
                "Transcription stop skipped:",
                error
            );

        }

    }
    if (liveChunkTimer) {

        clearInterval(
            liveChunkTimer
        );

        liveChunkTimer = null;
    }

    if (
        liveMediaRecorder &&
        liveMediaRecorder.state === "recording"
    ) {

        liveMediaRecorder.stop();
    }

    if (window.voiceShieldLiveMonitor) {
        window.voiceShieldLiveMonitor.stop();
    }

    stopLiveCallTimer();
    liveRiskHistory = [];
    updateLiveListeningState(false);
    if (!liveDecisionMade) {
        showLiveSecurityAnalyzing();
    }

    stopLiveVisualizer();

    liveMediaRecorder = null;

    if (liveMediaStream) {

        liveMediaStream
            .getTracks()
            .forEach(
                track => track.stop()
            );

        liveMediaStream = null;
    }

    updateLiveCallUI(false);

    if (chunkTimelineCard && chunkTimeline && chunkTimeline.children.length) {
        chunkTimelineCard.classList.remove("hidden");
    }

    if (dropZone) {
        dropZone.classList.remove("hidden");
    }

    if (analyzeButton) {
        analyzeButton.classList.remove("hidden");
    }

    /*
     * Finalize immediately when the user stops the live stream
     * after all queued chunk analyses have already completed.
     */
    if (livePendingAnalyses === 0) {
        finalizeLiveSecurityDecision();
    }

    console.log(
        "LIVE MICROPHONE STOPPED"
    );
    liveSpeechRecognition =
    null;

    liveTranscriptInterim =
        "";
}
function updateLiveCallUI(active) {

    const button =
        document.getElementById(
            "live-call-button"
        );

    const status =
        document.getElementById(
            "live-call-status"
        );

    if (button) {

        button.innerHTML = `
            <span class="mic-icon" aria-hidden="true"></span>
            ${active ? "STOP LIVE CALL" : "START LIVE CALL"}
        `;

        button.classList.toggle(
            "active",
            active
        );
    }

    if (status) {

        status.textContent =
            active
                ? "LISTENING"
                : "READY";
    }
}
/* ============================================================
   HANDLE REALTIME EVENTS
============================================================ */

function handleLiveCallEvent(event) {
    if (event && event.event === "chunk_analysis") {
        handleLiveAnalysisEvent({
            ...event,
            live_chunk_index: event.chunk_index
        });
        return;
    }

    if (!event || !event.event) {
        return;
    }


    /* --------------------------------------------------------
       CHUNK ANALYSIS
    -------------------------------------------------------- */

    if (
        event.event ===
        "chunk_analysis"
    ) {

        setLiveCallStatus(
            `LIVE MONITORING • CHUNK ${Number(event.chunk_index) + 1}/${event.total_chunks}`,
            "ready"
        );


        /*
         * Update prediction UI.
         */

        const prediction =
            String(
                event.prediction || "unknown"
            ).toLowerCase();


        if (voiceResult) {

            voiceResult.textContent =
                prediction.toUpperCase();

        }


        if (fakeScore) {

            fakeScore.textContent =
                formatPercent(
                    event.fake_score
                );

        }


        if (fakeScoreBar) {

            fakeScoreBar.style.width =
                `${Number(event.fake_score || 0) * 100}%`;

        }


        if (confidenceValue) {

            confidenceValue.textContent =
                formatPercent(
                    event.confidence
                );

        }


        if (confidenceBar) {

            confidenceBar.style.width =
                `${Number(event.confidence || 0) * 100}%`;

        }


        /*
         * Fake voice = immediate visual danger state.
         */

        if (
            prediction === "fake"
        ) {

            document.body.classList.add(
                "security-danger"
            );

        } else {

            document.body.classList.remove(
                "security-danger"
            );

        }


        /*
         * Update threat assessment
         * using the live chunk risk.
         */

        updateLiveRisk(
            event
        );


        /*
         * Add chunk to timeline.
         */

        addLiveChunk(
            event
        );

    }


    /* --------------------------------------------------------
       CALL COMPLETE
    -------------------------------------------------------- */

    else if (
        event.event ===
        "call_complete"
    ) {

        setLiveCallStatus(
            "CALL ANALYSIS COMPLETE",
            event.prediction === "fake"
                ? "blocked"
                : "ready"
        );


        /*
         * Final prediction.
         */

        const prediction =
            String(
                event.prediction || "unknown"
            ).toLowerCase();


        if (voiceResult) {

            voiceResult.textContent =
                prediction.toUpperCase();

        }


        if (fakeScore) {

            fakeScore.textContent =
                formatPercent(
                    event.average_fake_score
                );

        }


        if (confidenceValue) {

            confidenceValue.textContent =
                formatPercent(
                    event.confidence
                );

        }


        /*
         * Final security state.
         */

        if (
            prediction === "fake"
        ) {

            document.body.classList.add(
                "security-danger"
            );

            if (riskAction) {
                riskAction.textContent =
                    "BLOCK";
            }

        } else {

            document.body.classList.remove(
                "security-danger"
            );

            if (riskAction) {
                riskAction.textContent =
                    "ALLOW";
            }

        }

    }

}


/* ============================================================
   LIVE RISK UPDATE
============================================================ */

function updateLiveRisk(event) {

    const score =
        Number(
            event.risk_score || 0
        );

    const level =
        String(
            event.risk_level || "LOW"
        ).toUpperCase();

    const action =
        String(
            event.action || "ALLOW"
        ).toUpperCase();


    if (riskScore) {

        riskScore.textContent =
            Math.round(score);

    }


    if (riskLevel) {

        riskLevel.textContent =
            `${level} RISK`;

    }


    if (riskAction) {

        riskAction.textContent =
            action;

    }


    if (riskRing) {

        const circumference =
            578;

        const safeScore =
            Math.min(
                Math.max(score, 0),
                100
            );

        const offset =
            circumference -
            (safeScore / 100) *
            circumference;

        riskRing.style.strokeDashoffset =
            offset;

    }


    applyRiskStyle(
        level
    );

}


/* ============================================================
   ADD LIVE CHUNK TO TIMELINE
============================================================ */

function addLiveChunk(event) {

    if (!chunkTimeline) {
        return;
    }


    const fake =
        String(
            event.prediction
        ).toLowerCase() ===
        "fake";


    const element =
        document.createElement(
            "div"
        );


    element.className =
        fake
            ? "chunk fake"
            : "chunk";


    element.innerHTML = `
        <div class="chunk-index">
            CHUNK ${
                String(
                    Number(
                        event.chunk_index
                    ) + 1
                ).padStart(
                    2,
                    "0"
                )
            }
        </div>

        <div class="chunk-prediction">
            ${
                String(
                    event.prediction ||
                    "UNKNOWN"
                ).toUpperCase()
            }
        </div>

        <div class="chunk-score">
            ${
                formatPercent(
                    event.confidence
                )
            } confidence
        </div>
    `;


    chunkTimeline.appendChild(
        element
    );


    /*
     * Automatically reveal the latest chunk.
     */

    element.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });

}


/* ============================================================
   INITIALIZATION
============================================================ */

initializeGlassInteraction();

checkSystemHealth();


/* ============================================================
   CHALLENGE RESPONSE EVENT LISTENER
============================================================ */

window.addEventListener("voiceshield:challenge-required", (event) => {
    if (window.attachChallengeEvents && typeof window.attachChallengeEvents === "function") {
        window.attachChallengeEvents();
    }
});


/* ============================================================
   VOICESHIELD AI
   LIVE CALL VISUAL ENGINE
   ------------------------------------------------------------
   Additive only.
   Does NOT replace the existing live-call processing.
   ============================================================ */

(function initializeVoiceShieldLiveMonitor() {

    let vsAudioContext = null;
    let vsAnalyser = null;
    let vsMicrophone = null;
    let vsAnimationFrame = null;

    let vsCanvas = null;
    let vsCanvasContext = null;

    let vsLiveMonitor = null;
    let vsTimerElement = null;
    let vsListeningElement = null;
    let vsProcessingElement = null;

    let vsCallStartedAt = null;
    let vsTimerInterval = null;

    let vsLastChunk = -1;

    function findLiveSection() {

        return (
            document.getElementById("realtime-section") ||
            document.getElementById("live-call-section") ||
            document.querySelector(".realtime-section") ||
            document.querySelector(".live-call-section")
        );
    }

    function createMonitor() {

        if (vsLiveMonitor) {
            return;
        }

        const existingMonitor =
            document.querySelector(
                ".live-call-monitor"
            );

        if (existingMonitor) {
            vsLiveMonitor = existingMonitor;
            return;
        }

        const parent = findLiveSection();

        if (!parent) {

            console.warn(
                "VoiceShield Live Monitor: realtime section not found."
            );

            return;
        }

        vsLiveMonitor = document.createElement("div");
        vsLiveMonitor.className = "vs-live-monitor";

        vsLiveMonitor.innerHTML = `
            <div class="vs-live-status-row">
                <div class="vs-live-status">
                    <span class="vs-live-dot"></span>
                    <span id="vs-live-status-text">CALL STANDBY</span>
                </div>
                <div class="vs-live-timer" id="vs-live-timer">00:00</div>
            </div>

            <div class="vs-wave-container">
                <canvas id="vs-live-waveform"></canvas>
            </div>

            <div class="vs-listening-label" id="vs-listening-label">
                MICROPHONE READY
            </div>

            <div class="vs-live-processing" id="vs-live-processing">
                Waiting for call...
            </div>
        `;

        parent.appendChild(vsLiveMonitor);

        vsCanvas =
            document.getElementById("vs-live-waveform");

        vsCanvasContext =
            vsCanvas
                ? vsCanvas.getContext("2d")
                : null;

        vsTimerElement =
            document.getElementById("vs-live-timer");

        vsListeningElement =
            document.getElementById("vs-listening-label");

        vsProcessingElement =
            document.getElementById("vs-live-processing");

        resizeCanvas();

        window.addEventListener(
            "resize",
            resizeCanvas
        );
    }

    function resizeCanvas() {

        if (!vsCanvas) {
            return;
        }

        const rect =
            vsCanvas.getBoundingClientRect();

        const ratio =
            window.devicePixelRatio || 1;

        vsCanvas.width =
            rect.width * ratio;

        vsCanvas.height =
            rect.height * ratio;

        if (vsCanvasContext) {

            vsCanvasContext.setTransform(
                ratio,
                0,
                0,
                ratio,
                0,
                0
            );
        }
    }

    function drawIdleWave() {

        if (!vsCanvas || !vsCanvasContext) {
            return;
        }

        const width = vsCanvas.clientWidth;
        const height = vsCanvas.clientHeight;
        const center = height / 2;

        vsCanvasContext.clearRect(
            0,
            0,
            width,
            height
        );

        vsCanvasContext.beginPath();

        for (let x = 0; x < width; x++) {

            const y =
                center + Math.sin(x * 0.025) * 2;

            if (x === 0) {
                vsCanvasContext.moveTo(x, y);
            } else {
                vsCanvasContext.lineTo(x, y);
            }
        }

        vsCanvasContext.lineWidth = 1;
        vsCanvasContext.strokeStyle =
            "rgba(255,255,255,0.18)";
        vsCanvasContext.stroke();
    }

    function drawWaveform() {

        if (!vsAnalyser || !vsCanvas || !vsCanvasContext) {
            return;
        }

        const width = vsCanvas.clientWidth;
        const height = vsCanvas.clientHeight;
        const bufferLength = vsAnalyser.fftSize;
        const dataArray = new Uint8Array(bufferLength);

        function draw() {

            if (!vsAnalyser) {
                return;
            }

            vsAnimationFrame =
                requestAnimationFrame(draw);

            vsAnalyser.getByteTimeDomainData(
                dataArray
            );

            vsCanvasContext.clearRect(
                0,
                0,
                width,
                height
            );

            const center = height / 2;
            const sliceWidth = width / bufferLength;

            vsCanvasContext.beginPath();

            let x = 0;

            for (let i = 0; i < bufferLength; i++) {

                const normalized =
                    dataArray[i] / 128.0;

                const y = normalized * center;

                if (i === 0) {
                    vsCanvasContext.moveTo(x, y);
                } else {
                    vsCanvasContext.lineTo(x, y);
                }

                x += sliceWidth;
            }

            vsCanvasContext.lineWidth = 2;
            vsCanvasContext.strokeStyle =
                "rgba(255,255,255,0.85)";
            vsCanvasContext.stroke();
        }

        draw();
    }

    async function startMicrophoneVisualization(stream) {

        createMonitor();

        if (!stream) {
            console.warn("No microphone stream available.");
            return;
        }

        try {
            vsAudioContext =
                new (
                    window.AudioContext ||
                    window.webkitAudioContext
                )();

            vsAnalyser =
                vsAudioContext.createAnalyser();

            vsAnalyser.fftSize = 2048;
            vsAnalyser.smoothingTimeConstant = 0.75;

            vsMicrophone =
                vsAudioContext.createMediaStreamSource(
                    stream
                );

            vsMicrophone.connect(vsAnalyser);

            if (vsLiveMonitor) {
                vsLiveMonitor.classList.add("active");
                vsLiveMonitor.classList.remove("ended");
            }

            if (vsListeningElement) {
                vsListeningElement.textContent =
                    "LISTENING TO MICROPHONE";
                vsListeningElement.classList.add("active");
            }

            if (vsProcessingElement) {
                vsProcessingElement.textContent =
                    "Listening for incoming speech...";
            }

            drawWaveform();

        } catch (error) {

            console.error(
                "VoiceShield microphone visualization error:",
                error
            );

            if (vsListeningElement) {
                vsListeningElement.textContent =
                    "MICROPHONE ACCESS FAILED";
            }
        }
    }

    function stopMicrophoneVisualization() {

        if (vsAnimationFrame) {

            cancelAnimationFrame(vsAnimationFrame);
            vsAnimationFrame = null;
        }

        if (vsMicrophone) {

            try {
                vsMicrophone.disconnect();
            } catch (error) {}

            vsMicrophone = null;
        }

        if (vsAudioContext) {

            try {
                vsAudioContext.close();
            } catch (error) {}

            vsAudioContext = null;
        }

        vsAnalyser = null;

        if (vsLiveMonitor) {
            vsLiveMonitor.classList.remove("active");
            vsLiveMonitor.classList.add("ended");
        }

        if (vsListeningElement) {
            vsListeningElement.textContent = "CALL ENDED";
            vsListeningElement.classList.remove("active");
        }

        if (vsProcessingElement) {
            vsProcessingElement.textContent =
                "Live analysis stopped.";
        }

        drawIdleWave();
    }

    function startTimer() {

        vsCallStartedAt = Date.now();

        clearInterval(vsTimerInterval);

        vsTimerInterval =
            setInterval(updateTimer, 250);

        updateTimer();
    }

    function updateTimer() {

        if (!vsCallStartedAt || !vsTimerElement) {
            return;
        }

        const elapsed =
            Math.floor((Date.now() - vsCallStartedAt) / 1000);

        const minutes =
            Math.floor(elapsed / 60);

        const seconds = elapsed % 60;

        vsTimerElement.textContent =
            `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    }

    function stopTimer() {
        clearInterval(vsTimerInterval);
        vsTimerInterval = null;
    }

    window.voiceShieldLiveMonitor = {

        start: async function(stream) {

            createMonitor();
            startTimer();

            if (vsLiveMonitor) {
                vsLiveMonitor.classList.add("active");
            }

            const status =
                document.getElementById("vs-live-status-text");

            if (status) {
                status.textContent = "CALL ACTIVE";
            }

            await startMicrophoneVisualization(stream);
        },

        stop: function() {

            stopTimer();
            stopMicrophoneVisualization();

            const status =
                document.getElementById("vs-live-status-text");

            if (status) {
                status.textContent = "CALL ENDED";
            }
        },

        processing: function(chunkNumber) {

            createMonitor();

            if (vsLiveMonitor) {
                vsLiveMonitor.classList.add("processing");
            }

            if (vsProcessingElement) {
                vsProcessingElement.textContent =
                    `PROCESSING CHUNK ${String(
                        Number(chunkNumber) + 1
                    ).padStart(2, "0")}...`;
            }
        },

        analyzed: function(chunkNumber) {

            vsLastChunk = Number(chunkNumber);

            if (vsLiveMonitor) {
                vsLiveMonitor.classList.remove("processing");
            }

            if (vsProcessingElement) {
                vsProcessingElement.textContent =
                    `CHUNK ${String(
                        vsLastChunk + 1
                    ).padStart(2, "0")} ANALYZED - MONITORING CONTINUES`;
            }
        }
    };

    createMonitor();
    drawIdleWave();

})();