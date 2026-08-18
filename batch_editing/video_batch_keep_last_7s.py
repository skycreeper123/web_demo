from pathlib import Path
import sys

import cv2


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
KEEP_SECONDS = 7


def main():
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "input_videos"
    output_dir = base_dir / "output_last_7s"
    trimmed_dir = output_dir / "trimmed"
    frames_dir = output_dir / "first_frames"

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
        start_frame = max(0, total_frames - keep_frames)
        out_video = trimmed_dir / f"{video.stem}_last_7s.mp4"
        out_frame = frames_dir / f"{video.stem}_last_7s_first_frame.jpg"

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ok, first_frame = cap.read()
        if not ok:
            print(f"Cannot read start frame: {video.name}")
            cap.release()
            continue

        writer = cv2.VideoWriter(str(out_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        writer.write(first_frame)

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(frame)

        cap.release()
        writer.release()
        cv2.imwrite(str(out_frame), first_frame)
        print(f"Done: {out_video.name} / {out_frame.name}")

    print("All done.")


if __name__ == "__main__":
    main()
