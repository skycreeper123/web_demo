from pathlib import Path
import sys

import cv2


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
KEEP_SECONDS = 7


def main():
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "input_videos"
    output_dir = base_dir / "output_first_7s"
    trimmed_dir = output_dir / "trimmed"
    frames_dir = output_dir / "last_frames"

    if not input_dir.exists():
        print(f"Missing folder: {input_dir}")
        sys.exit(1)

    trimmed_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    videos = sorted([p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS])
    if not videos:
        print("No videos found.")
        sys.exit(1)

    for video in videos:
        print(f"Processing: {video.name}")
        cap = cv2.VideoCapture(str(video))
        if not cap.isOpened():
            print(f"Cannot open: {video.name}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps <= 0 or total_frames <= 0 or width <= 0 or height <= 0:
            print(f"Bad video info, skipped: {video.name}")
            cap.release()
            continue

        keep_frames = min(total_frames, max(1, int(fps * KEEP_SECONDS)))
        out_video = trimmed_dir / f"{video.stem}_first_7s.mp4"
        out_frame = frames_dir / f"{video.stem}_first_7s_last_frame.jpg"

        writer = cv2.VideoWriter(str(out_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        last_frame = None

        for _ in range(keep_frames):
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(frame)
            last_frame = frame

        cap.release()
        writer.release()

        if last_frame is not None:
            cv2.imwrite(str(out_frame), last_frame)
            print(f"Done: {out_video.name} / {out_frame.name}")

    print("All done.")


if __name__ == "__main__":
    main()
