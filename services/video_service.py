from pathlib import Path
import json
import subprocess

from config import (
    RAW_DIR,
    PROCESSED_DIR,
    CLIP_DIR,
)


SUPPORTED_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".webm",
}


def find_processed_videos():
    videos = []

    for path in PROCESSED_DIR.iterdir():
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        ):
            videos.append(path)

    return sorted(videos)


def generate_video_id():
    """
    ego_001
    ego_002
    ego_003
    ...
    """

    numbers = []

    for directory in [
        RAW_DIR,
        PROCESSED_DIR,
    ]:

        for path in directory.iterdir():

            if not path.is_file():
                continue

            stem = path.stem

            if not stem.startswith("ego_"):
                continue

            try:
                number = int(
                    stem.split("_")[1]
                )

                numbers.append(number)

            except (
                ValueError,
                IndexError,
            ):
                pass

    next_number = (
        max(numbers, default=0)
        + 1
    )

    return f"ego_{next_number:03d}"


def probe_video(video_path: Path):
    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr
        )

    return json.loads(
        result.stdout
    )


def extract_video_summary(metadata):
    video_stream = None

    for stream in metadata.get(
        "streams",
        [],
    ):

        if (
            stream.get("codec_type")
            == "video"
        ):

            video_stream = stream
            break

    if video_stream is None:
        raise ValueError(
            "Video stream을 찾을 수 없습니다."
        )

    fps_text = (
        video_stream.get(
            "avg_frame_rate",
            "0/1",
        )
    )

    try:
        numerator, denominator = (
            fps_text.split("/")
        )

        fps = (
            float(numerator)
            / float(denominator)
        )

    except Exception:
        fps = 0.0

    duration = (
        metadata
        .get("format", {})
        .get("duration", 0)
    )

    return {
        "width": int(
            video_stream.get(
                "width",
                0,
            )
        ),

        "height": int(
            video_stream.get(
                "height",
                0,
            )
        ),

        "codec": (
            video_stream.get(
                "codec_name",
                ""
            )
        ),

        "fps": round(
            fps,
            3,
        ),

        "duration": round(
            float(duration),
            3,
        ),
    }


def preprocess_video(
    input_path: Path,
    output_path: Path,
):
    """
    Annotation용 영상 표준화

    - 720p
    - 30 FPS
    - H.264
    - AAC (audio가 있을 경우)
    """

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(input_path),

        "-map",
        "0:v:0",

        "-map",
        "0:a?",

        "-vf",
        "scale=-2:720,fps=30",

        "-c:v",
        "libx264",

        "-crf",
        "23",

        "-preset",
        "medium",

        "-c:a",
        "aac",

        "-movflags",
        "+faststart",

        str(output_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr
        )


def extract_episode_clip(
    video_path: Path,
    video_id: str,
    episode_id: str,
    start_time: float,
    end_time: float,
):
    duration = (
        float(end_time)
        - float(start_time)
    )

    if duration <= 0:
        raise ValueError(
            "잘못된 Episode 시간입니다."
        )

    output_dir = (
        CLIP_DIR
        / video_id
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / f"{video_id}_{episode_id}.mp4"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(video_path),

        "-ss",
        f"{float(start_time):.3f}",

        "-t",
        f"{duration:.3f}",

        "-map",
        "0:v:0",

        "-map",
        "0:a?",

        "-c:v",
        "libx264",

        "-preset",
        "fast",

        "-crf",
        "20",

        "-c:a",
        "aac",

        "-movflags",
        "+faststart",

        str(output_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr
        )

    return output_path


def delete_episode_clip(
    video_id: str,
    episode_id: str,
):
    clip_path = (
        CLIP_DIR
        / video_id
        / f"{video_id}_{episode_id}.mp4"
    )

    if clip_path.exists():
        clip_path.unlink()