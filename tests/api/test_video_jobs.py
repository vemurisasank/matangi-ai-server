from api.routes.video import (
    create_video_job,
    get_video_job
)
from api.schemas.video_schema import AsyncVideoRequest
import pytest


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
