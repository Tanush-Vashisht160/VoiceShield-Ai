from pathlib import Path

from app.firewall import VoiceSecurityFirewall


REAL_AUDIO = Path(
    "data/release_in_the_wild/test/real/10004.wav"
)

FAKE_AUDIO = Path(
    "data/release_in_the_wild/test/fake/10012.wav"
)


# ================================================================
# SIMULATED TRANSCRIPTS
# ================================================================
# Speech-to-text is intentionally not implemented yet.
# These strings simulate the conversation transcript that will
# eventually come from an STT system.

REAL_CONVERSATION = """
Hello, this is a normal call. We wanted to discuss the project
meeting scheduled for tomorrow.
"""


FAKE_CONVERSATION = """
This is urgent. Your bank account will be blocked immediately.
Please tell me the OTP you received and send the money to this
bank account. Do not call the bank and do not disconnect.
"""


def print_result(result: dict):

    print("\n" + "=" * 70)
    print("VOICE SECURITY FIREWALL RESULT")
    print("=" * 70)

    print(f"Audio       : {result['audio_file']}")

    # ================================================================
    # VOICE AUTHENTICITY
    # ================================================================

    detection = result["voice_detection"]

    print("\nVOICE AUTHENTICITY")

    print(
        f"Prediction  : "
        f"{detection['prediction'].upper()}"
    )

    print(
        f"Fake score  : "
        f"{detection['fake_score']:.4f}"
    )

    print(
        f"Real score  : "
        f"{detection['real_score']:.4f}"
    )

    print(
        f"Confidence  : "
        f"{detection['confidence']:.4f}"
    )

    # ================================================================
    # SPEAKER VERIFICATION
    # ================================================================

    speaker = result["speaker_verification"]

    print("\nSPEAKER VERIFICATION")

    if speaker is None:

        print("Status      : NOT AVAILABLE")
        print(
            "Reason      : No reference speaker audio provided."
        )

    else:

        print(
            f"Same speaker: "
            f"{speaker['same_speaker']}"
        )

        print(
            f"Similarity  : "
            f"{speaker['score']:.4f}"
        )

        print(
            f"Reference   : "
            f"{speaker['reference_audio']}"
        )

    # ================================================================
    # SECURITY ASSESSMENT
    # ================================================================

    risk = result["risk"]
    decision = result["decision"]

    print("\n" + "=" * 70)
    print("AUTOMATED SECURITY RESPONSE")
    print("=" * 70)

    print(f"FINAL ACTION : {decision['action']}")
    print(f"RISK LEVEL   : {decision['level']}")
    print(f"RISK SCORE   : {decision['risk_score']}/100")

    print("\nThreat Analysis:")

    for alert in decision["alerts"]:
        print(f"  ⚠ {alert}")

    print("\nSystem Recommendation:")

    for recommendation in decision["recommended_actions"]:
        print(f"  → {recommendation}")

    print("\nExplanation:")
    print(f"  {decision['explanation']}")
    print("\nSECURITY ASSESSMENT")

    print(
        f"Risk score  : "
        f"{risk['score']}/100"
    )

    print(
        f"Risk level  : "
        f"{risk['level']}"
    )

    print(
        f"Action      : "
        f"{risk['action']}"
    )

    print("\nReasons:")

    for reason in risk["reasons"]:
        print(f"  - {reason}")


def main():

    print("Starting Voice Security Firewall...")

    firewall = VoiceSecurityFirewall()

    # ================================================================
    # DEMONSTRATION 1 — REAL CALL
    # ================================================================

    print("\nAnalyzing REAL sample...")

    result = firewall.analyze_call(
        audio_path=REAL_AUDIO,
        reference_audio=REAL_AUDIO,
        conversation_text=REAL_CONVERSATION,
    )

    print_result(result)

    # ================================================================
    # DEMONSTRATION 2 — FAKE CALL
    # ================================================================

    print("\n\nAnalyzing FAKE sample...")

    result = firewall.analyze_call(
        audio_path=FAKE_AUDIO,
        reference_audio=REAL_AUDIO,
        conversation_text=FAKE_CONVERSATION,
    )

    print_result(result)


if __name__ == "__main__":
    main()