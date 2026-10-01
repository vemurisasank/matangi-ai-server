from api.routes.video import (
    create_video_job,
    get_video_job
)
from api.schemas.video_schema import AsyncVideoRequest


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
