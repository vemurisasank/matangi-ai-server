import json
from pathlib import Path

from PIL import Image

import api.routes.video as video_route
from models.video_job import VideoJob


class Manager:
    def __init__(self, job=None):
        self.job = job

    def get_job(self, job_id):
        if self.job is not None and self.job.job_id == job_id:
            return self.job
        return None


def _response_payload(response):
    return json.loads(response.body.decode("utf-8"))


def test_last_frame_missing_job_returns_404(monkeypatch):
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        Manager()
    )

    response = video_route.get_video_job_last_frame("missing")

    assert response.status_code == 404
    assert _response_payload(response)["message"] == "Video job not found."


def test_last_frame_ready_returns_png(monkeypatch):
    frame_path = (
        video_route.CONTINUITY_ROOT
        / "test-api"
        / "scene"
        / "ready"
        / "last_frame.png"
    )
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    expected_bytes = None
    try:
        Image.new("RGB", (32, 16), color=(20, 40, 60)).save(
            frame_path,
            format="PNG"
        )
        expected_bytes = frame_path.read_bytes()
        monkeypatch.setattr(
            "api.routes.video.server.video_job_manager",
            Manager(
                VideoJob(
                    job_id="ready",
                    last_frame_path=str(frame_path),
                    last_frame_filename="last_frame.png",
                    last_frame_width=32,
                    last_frame_height=16,
                    last_frame_status="ready"
                )
            )
        )

        response = video_route.get_video_job_last_frame("ready")

        assert response.media_type == "image/png"
        assert Path(response.path).read_bytes() == expected_bytes
    finally:
        frame_path.unlink(missing_ok=True)


def test_last_frame_not_ready_returns_409(monkeypatch):
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        Manager(VideoJob(job_id="pending", last_frame_status="extracting"))
    )

    response = video_route.get_video_job_last_frame("pending")

    assert response.status_code == 409
    assert _response_payload(response)["message"] == "Last frame is not ready yet."


def test_last_frame_failed_returns_404(monkeypatch):
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        Manager(
            VideoJob(
                job_id="failed",
                last_frame_status="failed",
                last_frame_error="internal error"
            )
        )
    )

    response = video_route.get_video_job_last_frame("failed")

    assert response.status_code == 404
    assert _response_payload(response)["message"] == (
        "Last frame is unavailable because extraction failed."
    )
    assert "internal error" not in response.body.decode("utf-8")


def test_last_frame_missing_file_returns_404(monkeypatch):
    missing_path = video_route.CONTINUITY_ROOT / "missing" / "last_frame.png"
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        Manager(
            VideoJob(
                job_id="missing-file",
                last_frame_path=str(missing_path),
                last_frame_status="ready"
            )
        )
    )

    response = video_route.get_video_job_last_frame("missing-file")

    assert response.status_code == 404
    assert _response_payload(response)["message"] == "Last frame is unavailable."


def test_last_frame_outside_continuity_root_is_rejected(monkeypatch, tmp_path):
    outside_path = tmp_path / "secret.png"
    outside_path.write_bytes(b"not served")
    monkeypatch.setattr(
        "api.routes.video.server.video_job_manager",
        Manager(
            VideoJob(
                job_id="outside",
                last_frame_path=str(outside_path),
                last_frame_status="ready"
            )
        )
    )

    response = video_route.get_video_job_last_frame("outside")

    assert response.status_code == 404
    assert _response_payload(response)["message"] == "Last frame is unavailable."
