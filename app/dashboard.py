from pathlib import Path
import sys
import tempfile

# Ensure project root is available for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.firewall import VoiceSecurityFirewall

st.set_page_config(
    page_title="VoiceShield AI",
    page_icon="🛡️",
    layout="wide",
)


# ============================================================
# PAGE STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.75;
        margin-bottom: 25px;
    }

    .risk-card {
        padding: 25px;
        border-radius: 18px;
        text-align: center;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 15px;
    }

    .risk-score {
        font-size: 48px;
        font-weight: 800;
    }

    .decision {
        font-size: 30px;
        font-weight: 800;
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🛡️ VoiceShield AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    AI-Powered Real-Time Detection & Prevention of Voice Cloning
    Impersonation Attacks
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Call Analysis")

    audio_file = st.file_uploader(
        "Upload caller audio",
        type=["wav", "mp3", "flac", "ogg"],
    )

    reference_file = st.file_uploader(
        "Reference speaker audio",
        type=["wav", "mp3", "flac", "ogg"],
        help="Optional. Used to verify speaker identity.",
    )

    st.divider()

    st.subheader("🧠 Conversation")

    conversation_text = st.text_area(
        "Transcript / detected speech",
        placeholder=(
            "Example: "
            "Your account will be blocked. "
            "Please tell me the OTP and transfer the money."
        ),
        height=160,
    )

    analyze_button = st.button(
        "🔍 ANALYZE CALL",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# LOAD FIREWALL
# ============================================================

@st.cache_resource
def get_firewall():

    return VoiceSecurityFirewall()


# ============================================================
# WELCOME SCREEN
# ============================================================

if not analyze_button:

    st.info(
        "Upload a caller recording and optionally provide a "
        "reference voice. Then click **ANALYZE CALL**."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🤖 AI Detection",
            "ACTIVE",
        )

    with col2:
        st.metric(
            "👤 Speaker Verification",
            "ACTIVE",
        )

    with col3:
        st.metric(
            "🧠 Context Analysis",
            "ACTIVE",
        )

    st.divider()

    st.markdown("### 🔐 Multi-Layer Protection")

    st.markdown(
        """
        **VoiceShield AI combines multiple security signals:**

        - 🤖 AI-generated / deepfake voice detection
        - 👤 Speaker identity verification
        - 🧠 Suspicious conversation detection
        - ⚡ Dynamic risk scoring
        - 🚨 Automated ALLOW / WARN / BLOCK decision
        """
    )

    st.stop()


# ============================================================
# VALIDATION
# ============================================================

if audio_file is None:

    st.error(
        "Please upload a caller audio file first."
    )

    st.stop()


# ============================================================
# SAVE UPLOADED FILES
# ============================================================

try:

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = Path(temp_dir)

        audio_path = temp_dir / audio_file.name

        audio_path.write_bytes(
            audio_file.getbuffer()
        )

        reference_path = None

        if reference_file is not None:

            reference_path = (
                temp_dir / reference_file.name
            )

            reference_path.write_bytes(
                reference_file.getbuffer()
            )

        # ========================================================
        # RUN FIREWALL
        # ========================================================

        with st.spinner(
            "🔎 Running VoiceShield security analysis..."
        ):

            firewall = get_firewall()

            result = firewall.analyze_call(
                audio_path=audio_path,
                reference_audio=reference_path,
                transcript=(
                    conversation_text
                    if conversation_text.strip()
                    else None
                ),
            )


except Exception as exc:

    st.error(
        f"Analysis failed: {exc}"
    )

    st.stop()


# ============================================================
# EXTRACT RESULTS
# ============================================================

detection = result["voice_detection"]

speaker = result["speaker_verification"]

context = result["context_analysis"]

risk = result["risk"]

risk_score = float(risk["score"])


# ============================================================
# FINAL DECISION
# ============================================================

st.markdown("## 🚨 Security Decision")

decision_col, score_col = st.columns([1, 1])


with decision_col:

    if risk["action"] == "BLOCK":

        st.error(
            "🚫 CALL BLOCKED"
        )

    elif risk["action"] == "WARN":

        st.warning(
            "⚠️ CALL REQUIRES WARNING"
        )

    else:

        st.success(
            "✅ CALL ALLOWED"
        )


with score_col:

    st.metric(
        "Risk Score",
        f"{risk_score:.2f} / 100",
    )

    st.progress(
        min(max(risk_score / 100, 0.0), 1.0)
    )


st.divider()


# ============================================================
# THREE SECURITY SIGNALS
# ============================================================

st.markdown("## 🔬 Security Signals")

col1, col2, col3 = st.columns(3)


# ------------------------------------------------------------
# DEEPFAKE
# ------------------------------------------------------------

with col1:

    st.markdown("### 🤖 Voice Authenticity")

    prediction = detection["prediction"]

    if prediction == "fake":

        st.error("🔴 AI / FAKE VOICE")

    else:

        st.success("🟢 REAL VOICE")

    st.metric(
        "Fake Probability",
        f"{detection['fake_score'] * 100:.2f}%",
    )

    st.metric(
        "Confidence",
        f"{detection['confidence'] * 100:.2f}%",
    )


# ------------------------------------------------------------
# SPEAKER
# ------------------------------------------------------------

with col2:

    st.markdown("### 👤 Speaker Identity")

    if speaker is None:

        st.info(
            "Reference audio not provided."
        )

    else:

        if speaker["same_speaker"]:

            st.success(
                "🟢 SPEAKER MATCH"
            )

        else:

            st.error(
                "🔴 SPEAKER MISMATCH"
            )

        st.metric(
            "Similarity",
            f"{speaker['score']:.4f}",
        )


# ------------------------------------------------------------
# CONTEXT
# ------------------------------------------------------------

with col3:

    st.markdown("### 🧠 Conversation Risk")

    if context is None:

        st.info(
            "No conversation transcript provided."
        )

    else:

        context_score = (
            context["score"] * 100
        )

        if context["level"] == "HIGH":

            st.error("🔴 HIGH RISK")

        elif context["level"] == "MEDIUM":

            st.warning("🟡 MEDIUM RISK")

        else:

            st.success("🟢 LOW RISK")

        st.metric(
            "Context Risk",
            f"{context_score:.1f}%",
        )


# ============================================================
# REASONS
# ============================================================

st.divider()

st.markdown("## 🧠 Why was this decision made?")

if risk["reasons"]:

    for reason in risk["reasons"]:

        st.warning(
            f"• {reason}"
        )

else:

    st.success(
        "No significant security risks detected."
    )


# ============================================================
# TECHNICAL DETAILS
# ============================================================

# ============================================================
# TECHNICAL DETAILS
# ============================================================

with st.expander("🔧 Technical Analysis"):

    st.markdown("### 🎙️ Voice Detection")

    voice_col1, voice_col2, voice_col3, voice_col4 = st.columns(4)

    with voice_col1:
        st.metric(
            "Prediction",
            detection["prediction"].upper(),
        )

    with voice_col2:
        st.metric(
            "Fake Probability",
            f"{detection['fake_score'] * 100:.3f}%",
        )

    with voice_col3:
        st.metric(
            "Real Probability",
            f"{detection['real_score'] * 100:.3f}%",
        )

    with voice_col4:
        st.metric(
            "Confidence",
            f"{detection['confidence'] * 100:.3f}%",
        )

    st.divider()

    st.markdown("### 📊 Audio Analysis")

    audio_col1, audio_col2, audio_col3 = st.columns(3)

    with audio_col1:
        st.metric(
            "Total Chunks",
            detection.get("total_chunks", 0),
        )

    with audio_col2:
        st.metric(
            "Real Chunks",
            detection.get("real_chunks", 0),
        )

    with audio_col3:
        st.metric(
            "Fake Chunks",
            detection.get("fake_chunks", 0),
        )

    st.divider()

    st.markdown("### 👤 Speaker Verification")

    if speaker is None:

        st.info(
            "No reference speaker audio was provided."
        )

    else:

        speaker_col1, speaker_col2 = st.columns(2)

        with speaker_col1:
            st.metric(
                "Similarity",
                f"{speaker['score']:.4f}",
            )

        with speaker_col2:
            if speaker["same_speaker"]:
                st.success("🟢 Speaker Match")
            else:
                st.error("🔴 Speaker Mismatch")

    st.divider()

    st.markdown("### 🧠 Conversation Analysis")

    if context is None:

        st.info(
            "No conversation transcript was provided."
        )

    else:

        context_col1, context_col2, context_col3 = st.columns(3)

        with context_col1:
            st.metric(
                "Risk Score",
                f"{context['score'] * 100:.1f}%",
            )

        with context_col2:
            st.metric(
                "Risk Level",
                context["level"],
            )

        with context_col3:
            st.metric(
                "Action",
                context["action"],
            )

        if context.get("matched_categories"):

            st.markdown("**Detected Risk Categories:**")

            categories = context["matched_categories"]

            st.write(
                " • ".join(
                    category.replace("_", " ").title()
                    for category in categories
                )
            )

        if context.get("reasons"):

            st.markdown("**Detection Reasons:**")

            for reason in context["reasons"]:
                st.write(f"• {reason}")

    st.divider()

    st.markdown("### ⚠️ Final Risk Calculation")

    risk_col1, risk_col2, risk_col3 = st.columns(3)

    with risk_col1:
        st.metric(
            "Risk Score",
            f"{risk['score']:.2f} / 100",
        )

    with risk_col2:
        st.metric(
            "Risk Level",
            risk["level"],
        )

    with risk_col3:
        st.metric(
            "Action",
            risk["action"],
        )

    st.markdown("**Risk Inputs**")

    input_col1, input_col2, input_col3 = st.columns(3)

    with input_col1:
        st.metric(
            "Voice Risk",
            f"{risk['score']:.2f}",
        )

    with input_col2:
        st.metric(
            "Speaker Mismatch",
            f"{risk.get('speaker_mismatch_score', 0):.2f}",
        )

    with input_col3:
        st.metric(
            "Context Risk",
            f"{risk.get('context_risk_score', 0):.2f}",
        )