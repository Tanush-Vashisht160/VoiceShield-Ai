import os
import glob
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score
)

from app.detector import VoiceDeepfakeDetector


# ============================================================
# CONFIGURATION
# ============================================================

REAL_DIR = "dataset/test/real"
FAKE_DIR = "dataset/test/fake"

THRESHOLD = 0.50


# ============================================================
# LOAD MODEL
# ============================================================

detector = VoiceDeepfakeDetector()


# ============================================================
# FIND AUDIO FILES
# ============================================================

real_files = []
fake_files = []

for ext in ["*.wav", "*.mp3", "*.flac", "*.ogg", "*.m4a"]:
    real_files.extend(glob.glob(os.path.join(REAL_DIR, ext)))
    fake_files.extend(glob.glob(os.path.join(FAKE_DIR, ext)))


print("=" * 70)
print("           VOICESHIELD AI - MODEL EVALUATION")
print("=" * 70)

print(f"\nReal samples : {len(real_files)}")
print(f"Fake samples : {len(fake_files)}")
print(f"Total samples: {len(real_files) + len(fake_files)}")


# ============================================================
# PREDICTION
# ============================================================

y_true = []
y_pred = []
y_scores = []

print("\nRunning evaluation...\n")

# REAL = 0
for i, audio_file in enumerate(real_files, 1):

    try:
        result = detector.predict(audio_file)

        # CHANGE THIS LINE if your detector uses another key
        fake_score = float(result["fake_score"])

        prediction = 1 if fake_score >= THRESHOLD else 0

        y_true.append(0)
        y_pred.append(prediction)
        y_scores.append(fake_score)

        print(
            f"[REAL] {i:04d} | "
            f"score={fake_score:.3f} | "
            f"prediction={'FAKE' if prediction else 'REAL'}"
        )

    except Exception as e:
        print(f"[ERROR] {audio_file}: {e}")


# FAKE = 1
for i, audio_file in enumerate(fake_files, 1):

    try:
        result = detector.predict(audio_file)

        # CHANGE THIS LINE if your detector uses another key
        fake_score = float(result["fake_score"])

        prediction = 1 if fake_score >= THRESHOLD else 0

        y_true.append(1)
        y_pred.append(prediction)
        y_scores.append(fake_score)

        print(
            f"[FAKE] {i:04d} | "
            f"score={fake_score:.3f} | "
            f"prediction={'FAKE' if prediction else 'REAL'}"
        )

    except Exception as e:
        print(f"[ERROR] {audio_file}: {e}")


# ============================================================
# METRICS
# ============================================================

if len(y_true) == 0:
    print("\nNo samples were successfully evaluated.")
    exit()


accuracy = accuracy_score(y_true, y_pred)

precision = precision_score(
    y_true,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_true,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0
)

cm = confusion_matrix(y_true, y_pred)

print("\n")
print("=" * 70)
print("                    RESULTS")
print("=" * 70)

print(f"\nAccuracy  : {accuracy * 100:.2f}%")
print(f"Precision : {precision * 100:.2f}%")
print(f"Recall    : {recall * 100:.2f}%")
print(f"F1 Score  : {f1 * 100:.2f}%")


# ============================================================
# ROC-AUC
# ============================================================

try:

    auc = roc_auc_score(y_true, y_scores)

    print(f"ROC-AUC   : {auc * 100:.2f}%")

except Exception:
    print("ROC-AUC   : Not available")


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n" + "=" * 70)
print("                 CONFUSION MATRIX")
print("=" * 70)

print("\n                 Predicted")
print("               REAL     FAKE")
print(f"Actual REAL    {cm[0][0]:5d}    {cm[0][1]:5d}")
print(f"Actual FAKE    {cm[1][0]:5d}    {cm[1][1]:5d}")


# ============================================================
# DETAILED REPORT
# ============================================================

print("\n" + "=" * 70)
print("              CLASSIFICATION REPORT")
print("=" * 70)

print(
    classification_report(
        y_true,
        y_pred,
        target_names=["REAL", "FAKE"],
        digits=4,
        zero_division=0
    )
)

print("=" * 70)
print("Evaluation complete.")
print("=" * 70)