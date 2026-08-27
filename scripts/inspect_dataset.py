from pathlib import Path
import soundfile as sf


DATASET_ROOT = Path("data/release_in_the_wild")

SPLITS = ["train", "val", "test"]
LABELS = ["real", "fake"]


def get_audio_info(path: Path):
    try:
        info = sf.info(str(path))

        return (
            info.samplerate,
            info.channels,
            info.duration,
            info.format,
            info.subtype,
        )

    except Exception as e:
        return None, str(e)


def main():
    print("=" * 70)
    print("RELEASE IN THE WILD - DATASET INSPECTION")
    print("=" * 70)

    total_files = 0

    # ---------------------------------------------------------
    # DATASET COUNTS
    # ---------------------------------------------------------

    for split in SPLITS:
        print(f"\n[{split.upper()}]")

        split_total = 0

        for label in LABELS:
            folder = DATASET_ROOT / split / label

            if not folder.exists():
                print(f"  {label}: folder not found")
                continue

            files = list(folder.glob("*.wav"))
            count = len(files)

            split_total += count
            total_files += count

            print(f"  {label:5}: {count:,} files")

        print(f"  Total: {split_total:,}")

    # ---------------------------------------------------------
    # SAMPLE AUDIO INFORMATION
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("SAMPLE AUDIO INFORMATION")
    print("-" * 70)

    samples = []

    for split in SPLITS:
        for label in LABELS:
            folder = DATASET_ROOT / split / label

            if folder.exists():
                files = list(folder.glob("*.wav"))

                if files:
                    samples.append((split, label, files[0]))

    for split, label, path in samples:

        result = get_audio_info(path)

        if result[0] is not None:
            sample_rate, channels, duration, audio_format, subtype = result

            print(
                f"{split:5} | "
                f"{label:4} | "
                f"{path.name:15} | "
                f"{sample_rate:5} Hz | "
                f"{channels} ch | "
                f"{duration:.3f} sec | "
                f"{audio_format} | "
                f"{subtype}"
            )

        else:
            print(
                f"{split:5} | "
                f"{label:4} | "
                f"{path.name:15} | "
                f"Could not read: {result[1]}"
            )

    print("-" * 70)
    print(f"TOTAL AUDIO FILES: {total_files:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()