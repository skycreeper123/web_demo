from pathlib import Path
import sys

import cv2


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
KEEP_RATIO = 0.7


def process_video(video: Path, trimmed_dir: Path, frames_dir: Path):
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        print(f"Cannot open: {video.name}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if fps <= 0 or total_frames <= 0 or width <= 0 or height <= 0:
        print(f"Bad video info, skipped: {video.name}")
        cap.release()
        return

    keep_frames = max(1, int(total_frames * KEEP_RATIO))
    start_frame = max(0, total_frames - keep_frames)

    out_video = trimmed_dir / f"{video.stem}_last_70pct.mp4"
    out_frame = frames_dir / f"{video.stem}_last_70pct_first_frame.jpg"

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    ok, first_frame = cap.read()
    if not ok:
        print(f"Cannot read start frame: {video.name}")
        cap.release()
        return

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_video), fourcc, fps, (width, height))

    current = start_frame
    frame = first_frame
    while current < total_frames and frame is not None:
        writer.write(frame)
        ok, frame = cap.read()
        current += 1
        if not ok:
            break

    cap.release()
    writer.release()

    cv2.imwrite(str(out_frame), first_frame)
    print(f"Done: {out_video.name} / {out_frame.name}")


def main():
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "input_videos"
    output_dir = base_dir / "output_tail_70pct"
    trimmed_dir = output_dir / "trimmed"
    frames_dir = output_dir / "first_frames"

    if not input_dir.exists():
        print(f"Missing folder: {input_dir}")
        sys.exit(1)

    trimmed_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    videos = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS]
    if not videos:
        print("No videos found.")
        sys.exit(1)

    for video in videos:
        print(f"Processing: {video.name}")
        process_video(video, trimmed_dir, frames_dir)

    print("All done.")


if __name__ == "__main__":
    main()
