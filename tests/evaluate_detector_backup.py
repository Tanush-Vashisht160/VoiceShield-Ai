from pathlib import Path

from app.detector import DeepfakeDetector


REAL_DIR = Path("data/release_in_the_wild/test/real")
FAKE_DIR = Path("data/release_in_the_wild/test/fake")

SAMPLES_PER_CLASS = 20


def evaluate_class(
    detector: DeepfakeDetector,
    files: list[Path],
    expected: str,
) -> tuple[int, int, int]:
    correct = 0
    false_positives = 0
    false_negatives = 0

    print("\n" + "=" * 70)
    print(f"EXPECTED: {expected.upper()}")
    print("=" * 70)

    for index, audio_file in enumerate(files, start=1):
        result = detector.predict(audio_file)

        prediction = result["prediction"]
        fake_score = result["fake_score"]
        real_score = result["real_score"]

        is_correct = prediction == expected

        if is_correct:
            correct += 1
        elif expected == "real":
            false_positives += 1
        else:
            false_negatives += 1

        status = "OK" if is_correct else "WRONG"

        print(
            f"[{index:02d}/{len(files)}] "
            f"{audio_file.name:<20} "
            f"expected={expected:<4} "
            f"predicted={prediction:<4} "
            f"fake={fake_score:.4f} "
            f"real={real_score:.4f} "
            f"{status}"
        )

    return correct, false_positives, false_negatives


def main() -> None:
    print("Starting deepfake detector evaluation...")

    if not REAL_DIR.exists():
        raise FileNotFoundError(
            f"REAL directory not found: {REAL_DIR}"
        )

    if not FAKE_DIR.exists():
        raise FileNotFoundError(
            f"FAKE directory not found: {FAKE_DIR}"
        )

    real_files = sorted(
        path
        for path in REAL_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".wav", ".mp3", ".flac", ".ogg"}
    )[:SAMPLES_PER_CLASS]

    fake_files = sorted(
        path
        for path in FAKE_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".wav", ".mp3", ".flac", ".ogg"}
    )[:SAMPLES_PER_CLASS]

    if len(real_files) < SAMPLES_PER_CLASS:
        raise RuntimeError(
            f"Only found {len(real_files)} REAL files. "
            f"Need at least {SAMPLES_PER_CLASS}."
        )

    if len(fake_files) < SAMPLES_PER_CLASS:
        raise RuntimeError(
            f"Only found {len(fake_files)} FAKE files. "
            f"Need at least {SAMPLES_PER_CLASS}."
        )

    print(f"REAL samples: {len(real_files)}")
    print(f"FAKE samples: {len(fake_files)}")

    detector = DeepfakeDetector()

    real_correct, false_positives, _ = evaluate_class(
        detector,
        real_files,
        "real",
    )

    fake_correct, _, false_negatives = evaluate_class(
        detector,
        fake_files,
        "fake",
    )

    total = len(real_files) + len(fake_files)
    correct = real_correct + fake_correct
    accuracy = (correct / total) * 100

    print("\n" + "=" * 70)
    print("DETECTOR EVALUATION SUMMARY")
    print("=" * 70)

    print(f"Total samples       : {total}")
    print(f"Correct predictions : {correct}")
    print(f"Wrong predictions   : {total - correct}")
    print(f"Accuracy            : {accuracy:.2f}%")

    print("\nREAL CLASS")
    print(f"Correct REAL        : {real_correct}")
    print(f"False positives     : {false_positives}")

    print("\nFAKE CLASS")
    print(f"Correct FAKE        : {fake_correct}")
    print(f"False negatives     : {false_negatives}")

    print("\n" + "=" * 70)

    if accuracy >= 90:
        print("RESULT: EXCELLENT")
    elif accuracy >= 80:
        print("RESULT: GOOD")
    elif accuracy >= 70:
        print("RESULT: MODERATE")
    else:
        print("RESULT: POOR")

    print("=" * 70)


if __name__ == "__main__":
    main()