from pathlib import Path
import time
import argparse

from app.detector import DeepfakeDetector


REAL_DIR = Path("data/release_in_the_wild/test/real")
FAKE_DIR = Path("data/release_in_the_wild/test/fake")


def evaluate_directory(detector, files, expected, label):
    correct = 0
    wrong = 0

    start = time.time()

    print()
    print("=" * 70)
    print(f"{label}: {len(files)} files")
    print("=" * 70)

    for i, audio_file in enumerate(files, 1):

        result = detector.predict(audio_file)

        predicted = result["prediction"]

        if predicted == expected:
            correct += 1
        else:
            wrong += 1

        if i % 10 == 0 or i == len(files):
            elapsed = time.time() - start
            rate = i / elapsed if elapsed > 0 else 0

            print(
                f"{label}: "
                f"{i}/{len(files)} | "
                f"correct={correct} | "
                f"wrong={wrong} | "
                f"{rate:.2f} files/sec"
            )

    accuracy = correct / len(files) if files else 0.0

    return {
        "total": len(files),
        "correct": correct,
        "wrong": wrong,
        "accuracy": accuracy,
    }


def main():

    parser = argparse.ArgumentParser(
        description="Evaluate AntiDeepfake detector."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Total number of samples to evaluate. "
            "Split approximately equally between REAL and FAKE."
        ),
    )

    args = parser.parse_args()

    real_files = sorted(REAL_DIR.glob("*.wav"))
    fake_files = sorted(FAKE_DIR.glob("*.wav"))

    # ------------------------------------------------------------
    # Apply sample limit
    # ------------------------------------------------------------

    if args.limit is not None:

        if args.limit <= 0:
            raise ValueError("--limit must be greater than 0")

        real_limit = args.limit // 2
        fake_limit = args.limit - real_limit

        real_files = real_files[:real_limit]
        fake_files = fake_files[:fake_limit]

        evaluation_type = (
            f"LIMITED evaluation ({len(real_files)} REAL + "
            f"{len(fake_files)} FAKE)"
        )

    else:

        evaluation_type = "FULL Release in the Wild evaluation"

    # ------------------------------------------------------------
    # Print dataset information
    # ------------------------------------------------------------

    print("=" * 70)
    print(evaluation_type)
    print("=" * 70)

    print(f"REAL samples: {len(real_files)}")
    print(f"FAKE samples: {len(fake_files)}")
    print(f"TOTAL samples: {len(real_files) + len(fake_files)}")

    # ------------------------------------------------------------
    # Load detector
    # ------------------------------------------------------------

    detector = DeepfakeDetector()

    overall_start = time.time()

    # ------------------------------------------------------------
    # REAL
    # ------------------------------------------------------------

    real_results = evaluate_directory(
        detector,
        real_files,
        expected="real",
        label="REAL",
    )

    # ------------------------------------------------------------
    # FAKE
    # ------------------------------------------------------------

    fake_results = evaluate_directory(
        detector,
        fake_files,
        expected="fake",
        label="FAKE",
    )

    # ------------------------------------------------------------
    # Overall results
    # ------------------------------------------------------------

    total = (
        real_results["total"]
        + fake_results["total"]
    )

    correct = (
        real_results["correct"]
        + fake_results["correct"]
    )

    wrong = (
        real_results["wrong"]
        + fake_results["wrong"]
    )

    accuracy = correct / total if total else 0.0

    elapsed = time.time() - overall_start

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------

    print()
    print("=" * 70)

    if args.limit is not None:
        print("LIMITED EVALUATION SUMMARY")
    else:
        print("FULL EVALUATION SUMMARY")

    print("=" * 70)

    print(f"Total samples       : {total}")
    print(f"Correct predictions : {correct}")
    print(f"Wrong predictions   : {wrong}")
    print(f"Accuracy            : {accuracy * 100:.2f}%")

    print()
    print("REAL CLASS")
    print(f"Total REAL          : {real_results['total']}")
    print(f"Correct REAL        : {real_results['correct']}")
    print(f"False positives     : {real_results['wrong']}")
    print(
        f"REAL accuracy       : "
        f"{real_results['accuracy'] * 100:.2f}%"
    )

    print()
    print("FAKE CLASS")
    print(f"Total FAKE          : {fake_results['total']}")
    print(f"Correct FAKE        : {fake_results['correct']}")
    print(f"False negatives     : {fake_results['wrong']}")
    print(
        f"FAKE accuracy       : "
        f"{fake_results['accuracy'] * 100:.2f}%"
    )

    print()
    print(
        f"Evaluation time     : "
        f"{elapsed / 60:.2f} minutes"
    )

    print("=" * 70)

    if accuracy >= 0.95:
        print("RESULT: EXCELLENT")
    elif accuracy >= 0.90:
        print("RESULT: GOOD")
    elif accuracy >= 0.80:
        print("RESULT: ACCEPTABLE")
    else:
        print("RESULT: NEEDS INVESTIGATION")

    print("=" * 70)


if __name__ == "__main__":
    main()