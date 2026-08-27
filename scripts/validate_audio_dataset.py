from pathlib import Path
import soundfile as sf
from collections import Counter


DATASET_ROOT = Path("data/release_in_the_wild")

SPLITS = ["train", "val", "test"]
LABELS = ["real", "fake"]


def validate_file(path: Path):
    try:
        info = sf.info(str(path))

        if info.samplerate <= 0:
            return False, "invalid_sample_rate"

        if info.channels <= 0:
            return False, "invalid_channels"

        if info.duration <= 0:
            return False, "zero_duration"

        return True, info

    except Exception as e:
        return False, str(e)


def main():

    print("=" * 75)
    print("RELEASE IN THE WILD - FULL AUDIO VALIDATION")
    print("=" * 75)

    total = 0
    valid = 0
    invalid = 0

    errors = []

    sample_rates = Counter()
    channels = Counter()

    durations = []

    for split in SPLITS:

        print(f"\n[{split.upper()}]")

        for label in LABELS:

            folder = DATASET_ROOT / split / label

            files = list(folder.glob("*.wav"))

            label_total = len(files)
            label_valid = 0
            label_invalid = 0

            for path in files:

                total += 1

                ok, result = validate_file(path)

                if ok:
                    valid += 1
                    label_valid += 1

                    sample_rates[result.samplerate] += 1
                    channels[result.channels] += 1
                    durations.append(result.duration)

                else:
                    invalid += 1
                    label_invalid += 1

                    errors.append(
                        {
                            "split": split,
                            "label": label,
                            "file": str(path),
                            "error": str(result),
                        }
                    )

            print(
                f"  {label:5}: "
                f"{label_total:,} files | "
                f"valid: {label_valid:,} | "
                f"invalid: {label_invalid:,}"
            )

    print("\n" + "-" * 75)
    print("VALIDATION SUMMARY")
    print("-" * 75)

    print(f"Total files     : {total:,}")
    print(f"Valid files     : {valid:,}")
    print(f"Invalid files   : {invalid:,}")

    if total:
        print(f"Valid percentage: {(valid / total) * 100:.2f}%")

    print("\nSample rates:")
    for rate, count in sample_rates.items():
        print(f"  {rate} Hz : {count:,}")

    print("\nChannels:")
    for channel, count in channels.items():
        print(f"  {channel} channel(s): {count:,}")

    if durations:

        print("\nDuration statistics:")

        print(f"  Minimum : {min(durations):.3f} sec")
        print(f"  Maximum : {max(durations):.3f} sec")
        print(
            f"  Average : "
            f"{sum(durations) / len(durations):.3f} sec"
        )

    if errors:

        print("\n" + "-" * 75)
        print("FIRST 20 ERRORS")
        print("-" * 75)

        for error in errors[:20]:

            print(
                f"{error['split']} | "
                f"{error['label']} | "
                f"{error['file']} | "
                f"{error['error']}"
            )

    print("\n" + "=" * 75)

    if invalid == 0:
        print("RESULT: ALL AUDIO FILES ARE VALID")
    else:
        print(f"RESULT: {invalid:,} FILES NEED ATTENTION")

    print("=" * 75)


if __name__ == "__main__":
    main()