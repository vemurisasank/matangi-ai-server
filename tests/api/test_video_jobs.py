import sys
from types import ModuleType, SimpleNamespace

import pytest

# Avoid constructing unrelated providers while importing the route module.
if "core.server_context" not in sys.modules:
    test_server_context = ModuleType("core.server_context")
    test_server_context.server = SimpleNamespace(video_job_manager=None)
    sys.modules["core.server_context"] = test_server_context

from api.routes.video import (
    create_video_job,
    get_video_job
)
from api.schemas.video_schema import AsyncVideoRequest
from core import media_references


@pytest.fixture(autouse=True)
def staged_reference_files(monkeypatch, tmp_path):
    monkeypatch.setattr(media_references, "COMFY_INPUT_DIR", tmp_path)
    for filename in {
        "frame.png", "a.png", "b.png", "c.png",
        "1.png", "2.png", "3.png", "4.png", "5.png",
        "6.png", "7.png", "8.png", "9.png",
        "ganesha.png", "kailash.png"
    }:
        (tmp_path / filename).write_bytes(b"reference")


def test_h3_video_job_is_queued(monkeypatch):
    class Manager:
        def __init__(self):
            self.job = None

        def create_job(self, job):
            self.job = job

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )

    response = create_video_job(
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="scene",
            reference_image="frame.png"
        )
    )

    assert response["success"] is True
    assert response["data"]["status"] == "queued"
    assert manager.job.status == "queued"
    assert manager.job.progress is None


@pytest.mark.parametrize(
    "references",
    [
        ["a.png"],
        ["a.png", "b.png", "c.png"],
        [f"{index}.png" for index in range(1, 10)],
    ]
)
def test_h3_multi_reference_video_job_is_queued(monkeypatch, references):
    class Manager:
        def __init__(self):
            self.job = None

        def create_job(self, job):
            self.job = job

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )

    response = create_video_job(
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="scene",
            reference_images=references
        )
    )

    assert response["success"] is True
    assert manager.job.reference_images == references
    assert manager.job.reference_image is None


def test_h3_ten_references_are_rejected():
    with pytest.raises(ValueError):
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="scene",
            reference_images=[f"{index}.png" for index in range(10)]
        )


def test_h3_media_references_are_validated_and_persisted(monkeypatch):
    class Manager:
        def __init__(self):
            self.job = None

        def create_job(self, job):
            self.job = job

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )
    (media_references.COMFY_INPUT_DIR / "voice.wav").write_bytes(b"audio")
    (media_references.COMFY_INPUT_DIR / "reference.mp4").write_bytes(b"video")

    response = create_video_job(
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="scene",
            reference_image="frame.png",
            audio_references=["voice.wav"],
            video_references=["reference.mp4"]
        )
    )

    assert response["success"] is True
    assert manager.job.audio_references == ["voice.wav"]
    assert manager.job.video_references == ["reference.mp4"]


@pytest.mark.parametrize(
    ("field", "filename"),
    [
        ("reference_image", "missing.png"),
        ("audio_references", "missing.wav"),
        ("video_references", "missing.mp4"),
    ]
)
def test_h3_missing_media_reference_is_rejected(monkeypatch, field, filename):
    class Manager:
        def create_job(self, job):
            raise AssertionError("job should not be created")

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )
    fields = {
        "model": "minimax-h3",
        "prompt": "scene",
        "reference_image": "frame.png",
    }
    if field == "reference_image":
        fields[field] = filename
    else:
        fields[field] = [filename]

    response = create_video_job(AsyncVideoRequest(**fields))

    assert response["success"] is False


@pytest.mark.parametrize(
    ("field", "filename"),
    [
        ("reference_image", ""),
        ("reference_image", " "),
        ("reference_image", "/tmp/reference.png"),
        ("reference_image", r"C:\reference.png"),
        ("reference_image", "../reference.png"),
        ("reference_image", "nested/reference.png"),
        ("reference_image", r"nested\reference.png"),
        ("reference_image", "reference.gif"),
        ("audio_references", "voice.txt"),
        ("audio_references", "../voice.wav"),
        ("audio_references", r"C:\voice.wav"),
        ("video_references", "clip.txt"),
        ("video_references", "../clip.mp4"),
        ("video_references", r"C:\clip.mp4"),
    ]
)
def test_h3_invalid_media_reference_is_rejected(
    monkeypatch,
    field,
    filename
):
    class Manager:
        def create_job(self, job):
            raise AssertionError("job should not be created")

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )
    fields = {
        "model": "minimax-h3",
        "prompt": "scene",
        "reference_image": "frame.png",
    }
    if field == "reference_image":
        fields[field] = filename
    else:
        fields[field] = [filename]

    response = create_video_job(AsyncVideoRequest(**fields))

    assert response["success"] is False


@pytest.mark.parametrize(
    ("field", "filename", "extension"),
    [
        ("reference_image", "large.png", ".png"),
        ("audio_references", "large.wav", ".wav"),
        ("video_references", "large.mp4", ".mp4"),
    ]
)
def test_h3_media_reference_size_limit_is_enforced(
    monkeypatch,
    field,
    filename,
    extension
):
    class Manager:
        def create_job(self, job):
            raise AssertionError("job should not be created")

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )
    media_references.COMFY_INPUT_DIR.joinpath(filename).write_bytes(b"xx")
    original_limit = media_references.MEDIA_LIMITS[extension]
    media_references.MEDIA_LIMITS[extension] = 1
    try:
        fields = {
            "model": "minimax-h3",
            "prompt": "scene",
            "reference_image": "frame.png",
        }
        if field == "reference_image":
            fields[field] = filename
        else:
            fields[field] = [filename]

        response = create_video_job(AsyncVideoRequest(**fields))
    finally:
        media_references.MEDIA_LIMITS[extension] = original_limit

    assert response["success"] is False


def test_h3_reference_directories_and_escaping_symlinks_are_rejected(
    monkeypatch,
    tmp_path
):
    class Manager:
        def create_job(self, job):
            raise AssertionError("job should not be created")

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )
    (tmp_path / "folder.png").mkdir()
    outside = tmp_path.parent / "outside.png"
    outside.write_bytes(b"outside")
    symlink = tmp_path / "link.png"
    try:
        try:
            symlink.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are not supported")

        for filename in ("folder.png", "link.png"):
            response = create_video_job(
                AsyncVideoRequest(
                    model="minimax-h3",
                    prompt="scene",
                    reference_image=filename
                )
            )
            assert response["success"] is False
    finally:
        outside.unlink(missing_ok=True)


def test_h3_media_reference_limits_remain_enforced():
    with pytest.raises(ValueError):
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="scene",
            reference_image="frame.png",
            audio_references=["1.wav", "2.wav", "3.wav", "4.wav"]
        )
    with pytest.raises(ValueError):
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="scene",
            reference_image="frame.png",
            video_references=["1.mp4", "2.mp4", "3.mp4", "4.mp4"]
        )


def test_h3_media_references_default_to_empty_lists():
    request = AsyncVideoRequest(prompt="scene")

    assert request.audio_references == []
    assert request.video_references == []


@pytest.mark.parametrize(
    ("field", "references"),
    [
        ("audio_references", ["one.wav"]),
        ("audio_references", ["one.wav", "two.mp3", "three.flac"]),
        ("video_references", ["one.mp4"]),
        ("video_references", ["one.mp4", "two.webm", "three.mkv"]),
    ]
)
def test_h3_media_references_preserve_order(field, references):
    request = AsyncVideoRequest(
        prompt="scene",
        **{field: references}
    )

    assert getattr(request, field) == references


@pytest.mark.parametrize("field", ["audio_references", "video_references"])
def test_h3_media_references_limit_is_three(field):
    with pytest.raises(ValueError):
        AsyncVideoRequest(
            prompt="scene",
            **{field: [f"reference_{index}" for index in range(4)]}
        )


def test_h3_studio_reference_mapping_is_ordered(monkeypatch):
    class Manager:
        def __init__(self):
            self.job = None

        def create_job(self, job):
            self.job = job

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )

    response = create_video_job(
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="scene",
            ref_images={
                "ref_image_2": "c.png",
                "ref_image_0": "a.png",
                "ref_image_1": "b.png"
            }
        )
    )

    assert response["success"] is True
    assert manager.job.reference_images == ["a.png", "b.png", "c.png"]


def test_h3_reference_metadata_is_ordered_and_added_to_prompt(monkeypatch):
    class Manager:
        def __init__(self):
            self.job = None

        def create_job(self, job):
            self.job = job

    manager = Manager()
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        manager
    )

    response = create_video_job(
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="cinematic scene",
            reference_images=["ganesha.png", "kailash.png"],
            reference_metadata=[
                {"type": "CHARACTER", "name": "Ganesha"},
                {"type": "ENVIRONMENT", "name": "Mount Kailash"}
            ]
        )
    )

    assert response["success"] is True
    assert manager.job.reference_metadata == [
        {"type": "CHARACTER", "name": "Ganesha"},
        {"type": "ENVIRONMENT", "name": "Mount Kailash"}
    ]
    assert "cinematic scene" in manager.job.prompt
    assert "Reference 1" in manager.job.prompt
    assert "Asset: Ganesha" in manager.job.prompt
    assert "Uploaded file: ganesha.png" in manager.job.prompt
    assert "H3 slot: ref_images.ref_image_0" in manager.job.prompt
    assert "Reference 2" in manager.job.prompt
    assert "H3 slot: ref_images.ref_image_1" in manager.job.prompt


def test_h3_reference_metadata_length_must_match(monkeypatch):
    class Manager:
        def create_job(self, job):
            raise AssertionError("job should not be created")

    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        Manager()
    )

    response = create_video_job(
        AsyncVideoRequest(
            model="minimax-h3",
            prompt="scene",
            reference_images=["a.png", "b.png"],
            reference_metadata=[{"type": "CHARACTER", "name": "A"}]
        )
    )

    assert response["success"] is False


def test_h3_video_job_requires_explicit_model():
    response = create_video_job(
        AsyncVideoRequest(
            prompt="scene",
            reference_image="frame.png"
        )
    )

    assert response["success"] is False


def test_video_job_status_does_not_include_base64(monkeypatch):
    class Manager:
        def get_job(self, _job_id):
            from models.video_job import VideoJob
            return VideoJob(
                job_id="job-1",
                status="completed",
                progress=100,
                output_filename="video.mp4"
            )

    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        Manager()
    )

    response = get_video_job("job-1")

    assert response["success"] is True
    assert "video_base64" not in response["data"]
