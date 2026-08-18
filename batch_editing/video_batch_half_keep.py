from pathlib import Path
import subprocess
import sys


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def get_duration(video_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def main():
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "input_videos"
    output_dir = base_dir / "output"
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
        duration = get_duration(video)
        half = duration / 2

        out_video = trimmed_dir / f"{video.stem}_first_half{video.suffix}"
        out_frame = frames_dir / f"{video.stem}_half_last_frame.jpg"

        # 保留前 50% 时长的视频
        run([
            "ffmpeg",
            "-y",
            "-i", str(video),
            "-t", f"{half}",
            "-c", "copy",
            str(out_video),
        ])

        # 提取前 50% 结束时那一帧
        # 这里取 half 前 0.05 秒，通常更稳一点
        seek_time = max(0.0, half - 0.05)
        run([
            "ffmpeg",
            "-y",
            "-ss", f"{seek_time}",
            "-i", str(video),
            "-frames:v", "1",
            str(out_frame),
        ])

        print(f"完成：{out_video.name} / {out_frame.name}")

    print("全部处理完成。")


if __name__ == "__main__":
    main()
