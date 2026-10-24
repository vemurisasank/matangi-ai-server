import asyncio
import io
from pathlib import Path

import pytest

from api.routes import upload
from core import media_references


class FakeUpload:
    def __init__(self, filename, content, chunk_size=None):
        self.filename = filename
        self._stream = io.BytesIO(content)
        self._chunk_size = chunk_size
        self.closed = False

    async def read(self, size=-1):
        if self._chunk_size is not None:
            size = min(size, self._chunk_size)
        return self._stream.read(size)

    async def close(self):
        self.closed = True


class SizedUpload:
    def __init__(self, filename, size, chunk_size=1024):
        self.filename = filename
        self.remaining = size
        self.chunk_size = chunk_size
        self.closed = False

    async def read(self, size=-1):
        if self.remaining == 0:
            return b""
        amount = min(self.remaining, size, self.chunk_size)
        self.remaining -= amount
        return b"x" * amount

    async def close(self):
        self.closed = True


def run_upload(monkeypatch, tmp_path, filename, content, chunk_size=None):
    monkeypatch.setattr(media_references, "COMFY_INPUT_DIR", tmp_path)
    return asyncio.run(
        upload.upload_reference(
            FakeUpload(filename, content, chunk_size=chunk_size)
        )
    )


def run_sized_upload(monkeypatch, tmp_path, filename, size, chunk_size=1024):
    monkeypatch.setattr(media_references, "COMFY_INPUT_DIR", tmp_path)
    return asyncio.run(
        upload.upload_reference(
            SizedUpload(filename, size, chunk_size=chunk_size)
        )
    )


def test_image_upload_preserves_response_contract(monkeypatch, tmp_path):
    response = run_upload(
        monkeypatch,
        tmp_path,
        "reference.PNG",
        b"image",
    )

    assert response["success"] is True
    assert response["message"] == "Reference image uploaded successfully."
    assert set(response["data"]) == {"filename"}
    destination = tmp_path / response["data"]["filename"]
    assert destination.is_file()
    assert destination.read_bytes() == b"image"


@pytest.mark.parametrize(
    "filename",
    ["reference.wav", "reference.mp3", "reference.flac", "reference.m4a",
     "reference.aac", "reference.ogg", "reference.oga",
     "reference.mp4", "reference.mov", "reference.mkv", "reference.webm",
     "reference.avi"],
)
def test_supported_audio_and_video_extensions_are_accepted(
    monkeypatch,
    tmp_path,
    filename,
):
    response = run_upload(monkeypatch, tmp_path, filename, b"media")

    assert response["success"] is True
    assert (tmp_path / response["data"]["filename"]).read_bytes() == b"media"


@pytest.mark.parametrize("filename", ["", "reference.txt", None])
def test_empty_and_unsupported_filenames_are_rejected(
    monkeypatch,
    tmp_path,
    filename,
):
    response = run_upload(monkeypatch, tmp_path, filename, b"media")

    assert response == {
        "success": False,
        "message": "Unsupported reference file format.",
        "data": None,
    }
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("filename", "limit"),
    [
        ("reference.png", 20 * 1024 * 1024),
        ("reference.wav", 50 * 1024 * 1024),
        ("reference.mp4", 200 * 1024 * 1024),
    ],
)
def test_each_media_category_enforces_its_limit(
    monkeypatch,
    tmp_path,
    filename,
    limit,
):
    response = run_sized_upload(
        monkeypatch,
        tmp_path,
        filename,
        limit + 1,
        chunk_size=3,
    )

    assert response["success"] is False
    assert response["message"] == "Uploaded file exceeds the permitted size."
    assert list(tmp_path.iterdir()) == []


def test_oversized_stream_is_rejected_without_partial_destination(
    monkeypatch,
    tmp_path,
):
    response = run_sized_upload(
        monkeypatch,
        tmp_path,
        "reference.png",
        20 * 1024 * 1024 + 1,
        chunk_size=1024,
    )

    assert response["success"] is False
    assert list(tmp_path.iterdir()) == []


def test_destination_is_generated_basename_inside_input_directory(
    monkeypatch,
    tmp_path,
):
    response = run_upload(
        monkeypatch,
        tmp_path,
        "../outside.png",
        b"image",
    )

    assert response["success"] is True
    generated = response["data"]["filename"]
    assert Path(generated).name == generated
    assert (tmp_path / generated).is_file()
    assert not (tmp_path.parent / "outside.png").exists()


def test_existing_destination_is_not_overwritten(monkeypatch, tmp_path):
    monkeypatch.setattr(
        upload.uuid,
        "uuid4",
        lambda: type("Uuid", (), {"hex": "fixed"})(),
    )

    first = run_upload(monkeypatch, tmp_path, "first.png", b"first")
    second = run_upload(monkeypatch, tmp_path, "second.png", b"second")

    destination = tmp_path / first["data"]["filename"]
    assert first["success"] is True
    assert second["success"] is False
    assert second["message"] == "Unable to store the uploaded reference file."
    assert destination.read_bytes() == b"first"
