from pathlib import Path
import sys

import cv2


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
KEEP_RATIO = 0.7


def main():
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "input_videos"
    output_dir = base_dir / "output_70pct"
    trimmed_dir = output_dir / "trimmed"
    frames_dir = output_dir / "last_frames"

    if not input_dir.exists():
        print(f"找不到输入文件夹：{input_dir}")
        print("请先创建 input_videos 文件夹，并把视频放进去。")
        sys.exit(1)

    trimmed_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    videos = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS]
    if not videos:
        print(f"在 {input_dir} 里没有找到视频文件。")
        sys.exit(1)

    for video in videos:
        print(f"处理：{video.name}")

        cap = cv2.VideoCapture(str(video))
        if not cap.isOpened():
            print(f"无法打开，跳过：{video.name}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps <= 0 or total_frames <= 0 or width <= 0 or height <= 0:
            print(f"无法读取视频信息，跳过：{video.name}")
            cap.release()
            continue

        keep_frames = max(1, int(total_frames * KEEP_RATIO))
        out_video = trimmed_dir / f"{video.stem}_first_70pct.mp4"
        out_frame = frames_dir / f"{video.stem}_70pct_last_frame.jpg"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_video), fourcc, fps, (width, height))

        last_frame = None
        written = 0

        while written < keep_frames:
            ok, frame = cap.read()
            if not ok:
                break

            writer.write(frame)
            last_frame = frame
            written += 1

        cap.release()
        writer.release()

        if last_frame is not None:
            cv2.imwrite(str(out_frame), last_frame)
            print(f"完成：{out_video.name} / {out_frame.name}")
        else:
            print(f"没有成功读取画面，跳过：{video.name}")

    print("全部处理完成。")


if __name__ == "__main__":
    main()
