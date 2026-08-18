from pathlib import Path
import sys

import cv2


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def list_videos(folder: Path):
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS])


def write_video_part(writer, video_path: Path, target_size):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path.name}")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if (frame.shape[1], frame.shape[0]) != target_size:
            frame = cv2.resize(frame, target_size)
        writer.write(frame)

    cap.release()


def main():
    base_dir = Path(__file__).resolve().parent
    folder_a = base_dir / "input_folder_a"
    folder_b = base_dir / "input_folder_b"
    output_dir = base_dir / "output_merged_pairs"

    if not folder_a.exists():
        print(f"Missing folder: {folder_a}")
        sys.exit(1)
    if not folder_b.exists():
        print(f"Missing folder: {folder_b}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    videos_a = list_videos(folder_a)
    videos_b = list_videos(folder_b)

    if not videos_a:
        print(f"No videos found in {folder_a}")
        sys.exit(1)
    if not videos_b:
        print(f"No videos found in {folder_b}")
        sys.exit(1)

    pair_count = min(len(videos_a), len(videos_b))
    if len(videos_a) != len(videos_b):
        print(f"Warning: folder counts differ, only merging first {pair_count} pairs.")

    for idx in range(pair_count):
        video_a = videos_a[idx]
        video_b = videos_b[idx]
        print(f"Merging pair {idx + 1}: {video_a.name} + {video_b.name}")

        cap_a = cv2.VideoCapture(str(video_a))
        if not cap_a.isOpened():
            print(f"Cannot open: {video_a.name}, skipped.")
            continue

        fps = cap_a.get(cv2.CAP_PROP_FPS)
        width = int(cap_a.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap_a.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap_a.release()

        if fps <= 0 or width <= 0 or height <= 0:
            print(f"Bad video info: {video_a.name}, skipped.")
            continue

        out_path = output_dir / f"{video_a.stem}__{video_b.stem}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

        try:
            write_video_part(writer, video_a, (width, height))
            write_video_part(writer, video_b, (width, height))
        except Exception as exc:
            print(f"Failed on pair {idx + 1}: {exc}")
        finally:
            writer.release()

        print(f"Saved: {out_path.name}")

    print("All done.")


if __name__ == "__main__":
    main()
