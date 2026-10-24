import json
from pathlib import Path

import pytest
from PIL import Image

import core.video_frames as video_frames


OUTPUT_ROOT = Path("/workspace/ComfyUI/output")


def _source_fixture():
    source = OUTPUT_ROOT / ".test_video_frames_source.mp4"
    source.write_bytes(b"mock video")
    return source


def test_source_outside_comfy_output_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="inside"):
        video_frames.extract_last_frame(
            tmp_path / "outside.mp4",
            tmp_path / "last_frame.png"
        )


def test_missing_source_is_rejected():
    source = OUTPUT_ROOT / ".missing_video_frames_source.mp4"
    with pytest.raises(FileNotFoundError):
        video_frames.extract_last_frame(
            source,
            OUTPUT_ROOT / ".test_last_frame.png"
        )


def test_successful_extraction_counts_frames_and_atomically_replaces_output(
    monkeypatch,
    tmp_path
):
    source = _source_fixture()
    destination = tmp_path / "last_frame.png"
    destination.write_bytes(b"old output")
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[0] == "ffprobe":
            return _CompletedProcess(
                0,
                json.dumps({
                    "streams": [{
                        "codec_type": "video",
                        "width": 1024,
                        "height": 704,
                        "nb_read_frames": "447"
                    }]
                }),
                ""
            )

        temporary_path = Path(command[-1])
        Image.new("RGB", (1024, 704), color="black").save(
            temporary_path,
            format="PNG"
        )
        return _CompletedProcess(0, "", "")

    monkeypatch.setattr(video_frames.subprocess, "run", fake_run)
    try:
        result = video_frames.extract_last_frame(source, destination)
    finally:
        source.unlink(missing_ok=True)

    assert result.output_path == str(destination.resolve())
    assert result.width == 1024
    assert result.height == 704
    assert result.frame_count == 447
    assert result.frame_index == 446
    assert Image.open(destination).size == (1024, 704)
    assert commands[1][0] == "ffmpeg"
    assert "select=eq(n\\,446)" in commands[1]
    assert not list(destination.parent.glob(f".{destination.name}.*.tmp.png"))


def test_failed_extraction_removes_temporary_png(monkeypatch, tmp_path):
    source = _source_fixture()
    destination = tmp_path / "last_frame.png"

    def fake_run(command, **kwargs):
        if command[0] == "ffprobe":
            return _CompletedProcess(
                0,
                json.dumps({
                    "streams": [{
                        "codec_type": "video",
                        "width": 640,
                        "height": 352,
                        "nb_read_frames": "124"
                    }]
                }),
                ""
            )
        return _CompletedProcess(1, "", "decode failed")

    monkeypatch.setattr(video_frames.subprocess, "run", fake_run)
    try:
        with pytest.raises(video_frames.VideoFrameExtractionError):
            video_frames.extract_last_frame(source, destination)
    finally:
        source.unlink(missing_ok=True)

    assert not destination.exists()
    assert not list(destination.parent.glob(f".{destination.name}.*.tmp.png"))


class _CompletedProcess:
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
