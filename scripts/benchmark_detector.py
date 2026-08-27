from pathlib import Path
import time

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from transformers import pipeline


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "MelodyMachine/Deepfake-audio-detection-V2"

TEST_DIR = Path("data/release_in_the_wild/test")

SAMPLES_PER_CLASS = 100


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 70)
print("VOICE SECURITY FIREWALL - DETECTOR BENCHMARK")
print("=" * 70)

print("\nLoading deepfake audio detector...")

detector = pipeline(
    "audio-classification",
    model=MODEL_NAME,
)

print("Model loaded successfully!")


# ============================================================
# FIND AUDIO FILES
# ============================================================

real_files = sorted(
    (TEST_DIR / "real").glob("*.wav")
)[:SAMPLES_PER_CLASS]

fake_files = sorted(
    (TEST_DIR / "fake").glob("*.wav")
)[:SAMPLES_PER_CLASS]


print("\nDataset:")
print(f"  Real samples: {len(real_files)}")
print(f"  Fake samples: {len(fake_files)}")


if len(real_files) < SAMPLES_PER_CLASS:
    raise RuntimeError("Not enough real audio files.")

if len(fake_files) < SAMPLES_PER_CLASS:
    raise RuntimeError("Not enough fake audio files.")


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def get_prediction(audio_file: Path):
    start = time.perf_counter()

    result = detector(str(audio_file))

    elapsed = time.perf_counter() - start

    # Find probability assigned to "fake"
    fake_score = next(
        item["score"]
        for item in result
        if item["label"].lower() == "fake"
    )

    predicted_label = 1 if fake_score >= 0.5 else 0

    return predicted_label, fake_score, elapsed


# ============================================================
# RUN BENCHMARK
# ============================================================

y_true = []
y_pred = []
fake_scores = []
inference_times = []


all_files = []

for audio_file in real_files:
    all_files.append((audio_file, 0))

for audio_file in fake_files:
    all_files.append((audio_file, 1))


print("\nRunning inference...")
print("-" * 70)


for index, (audio_file, true_label) in enumerate(all_files, start=1):

    predicted_label, fake_score, elapsed = get_prediction(audio_file)

    y_true.append(true_label)
    y_pred.append(predicted_label)

    fake_scores.append(fake_score)
    inference_times.append(elapsed)

    if index % 20 == 0 or index == len(all_files):
        print(
            f"Processed {index:3d}/{len(all_files)} | "
            f"Last: {audio_file.name} | "
            f"Fake score: {fake_score:.4f}"
        )


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(y_true, y_pred)

precision = precision_score(
    y_true,
    y_pred,
    zero_division=0,
)

recall = recall_score(
    y_true,
    y_pred,
    zero_division=0,
)

f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0,
)

matrix = confusion_matrix(y_true, y_pred)

average_time = np.mean(inference_times)


# ============================================================
# RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("BENCHMARK RESULTS")
print("=" * 70)

print(f"\nAccuracy       : {accuracy:.4f}")
print(f"Precision      : {precision:.4f}")
print(f"Recall         : {recall:.4f}")
print(f"F1 Score       : {f1:.4f}")
print(f"Avg inference  : {average_time:.3f} sec/audio")

print("\nConfusion Matrix:")
print(matrix)

print("\nClassification Report:")
print(
    classification_report(
        y_true,
        y_pred,
        target_names=["REAL", "FAKE"],
        zero_division=0,
    )
)

print("=" * 70)