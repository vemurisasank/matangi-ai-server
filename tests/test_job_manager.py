import json

from api.routes.image import get_image_job
from core.job_manager import JobManager
from models.job import Job


def make_job(job_id="job-1"):
    return Job(
        id=job_id,
        type="image",
        provider="comfyui",
        model="qwen-image-edit-2511",
        status="queued",
        progress=0
    )


def test_job_lifecycle_persists_and_reloads(tmp_path):
    storage_path = tmp_path / "image_jobs.json"
    manager = JobManager(storage_path=storage_path)
    job = make_job()

    manager.create(job)
    assert storage_path.exists()
    assert json.loads(storage_path.read_text()) [0]["status"] == "queued"

    job.status = "running"
    job.started_on = "2026-09-27T05:00:00"
    manager.persist(job)

    job.status = "completed"
    job.progress = 100
    job.completed_on = "2026-09-27T05:01:00"
    job.result = {
        "success": True,
        "provider": "ComfyUI",
        "image_base64": "encoded"
    }
    manager.persist(job)

    reloaded = JobManager(storage_path=storage_path)
    restored = reloaded.get(job.id)

    assert restored is not None
    assert restored.status == "completed"
    assert restored.progress == 100
    assert restored.result == job.result


def test_image_job_route_returns_reloaded_completed_result(tmp_path, monkeypatch):
    storage_path = tmp_path / "image_jobs.json"
    manager = JobManager(storage_path=storage_path)
    job = make_job("job-route")
    job.status = "completed"
    job.progress = 100
    job.result = {"success": True, "image_base64": "encoded"}
    manager.create(job)

    import api.routes.image as image_route

    monkeypatch.setattr(image_route.server, "job_manager", manager)
    response = get_image_job(job.id)

    assert response["success"] is True
    assert response["data"]["result"] == job.result
