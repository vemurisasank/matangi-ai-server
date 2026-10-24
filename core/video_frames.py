import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


COMFY_OUTPUT_DIR = Path("/workspace/ComfyUI/output").resolve()
FFPROBE = "ffprobe"
FFMPEG = "ffmpeg"


class VideoFrameExtractionError(RuntimeError):
    """Raised when a final video frame cannot be extracted safely."""


@dataclass(frozen=True)
class VideoFrameResult:
    output_path: str
    width: int
    height: int
    frame_index: int
    frame_count: int
    status: str = "success"


def extract_last_frame(source_video, output_path) -> VideoFrameResult:
    source = _validated_source_path(source_video)
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    stream = _probe_video(source)
    frame_count = stream["frame_count"]
    width = stream["width"]
    height = stream["height"]
    frame_index = frame_count - 1

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp.png",
            delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        _extract_frame(source, temporary_path, frame_index)
        _validate_png(temporary_path, width, height)
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return VideoFrameResult(
        output_path=str(destination),
        width=width,
        height=height,
        frame_index=frame_index,
        frame_count=frame_count
    )


def _validated_source_path(source_video) -> Path:
    source = Path(source_video).resolve()
    if COMFY_OUTPUT_DIR not in source.parents:
        raise ValueError(
            f"Source video must be inside {COMFY_OUTPUT_DIR}: {source}"
        )
    if not source.is_file():
        raise FileNotFoundError(f"Source video was not found: {source}")
    return source


def _probe_video(source: Path) -> dict[str, int]:
    command = [
        FFPROBE,
        "-v",
        "error",
        "-count_frames",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_type,width,height,nb_read_frames",
        "-of",
        "json",
        str(source)
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise VideoFrameExtractionError(
            f"ffprobe failed for {source}: {result.stderr.strip()}"
        )

    try:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        codec_type = stream["codec_type"]
        width = int(stream["width"])
        height = int(stream["height"])
        frame_count = int(stream["nb_read_frames"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise VideoFrameExtractionError(
            f"ffprobe returned invalid video metadata for {source}."
        ) from error

    if codec_type != "video":
        raise VideoFrameExtractionError(
            f"ffprobe did not find a video stream in {source}."
        )
    if width <= 0 or height <= 0:
        raise VideoFrameExtractionError(
            f"Video dimensions are invalid for {source}: {width}x{height}."
        )
    if frame_count <= 0:
        raise VideoFrameExtractionError(
            f"Video has no decoded frames: {source}"
        )

    return {
        "width": width,
        "height": height,
        "frame_count": frame_count
    }


def _extract_frame(source: Path, destination: Path, frame_index: int) -> None:
    command = [
        FFMPEG,
        "-v",
        "error",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-vf",
        f"select=eq(n\\,{frame_index})",
        "-fps_mode",
        "vfr",
        "-frames:v",
        "1",
        "-y",
        str(destination)
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise VideoFrameExtractionError(
            f"ffmpeg failed to extract the final frame from {source}: "
            f"{result.stderr.strip()}"
        )


def _validate_png(path: Path, expected_width: int, expected_height: int) -> None:
    if not path.is_file():
        raise VideoFrameExtractionError(
            f"ffmpeg did not produce the expected frame: {path}"
        )

    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
    except (OSError, ValueError) as error:
        raise VideoFrameExtractionError(
            f"Extracted frame is not a readable image: {path}"
        ) from error

    if width <= 0 or height <= 0:
        raise VideoFrameExtractionError(
            f"Extracted frame dimensions are invalid: {width}x{height}."
        )
    if (width, height) != (expected_width, expected_height):
        raise VideoFrameExtractionError(
            "Extracted frame dimensions do not match the video stream: "
            f"{width}x{height} != {expected_width}x{expected_height}."
        )
