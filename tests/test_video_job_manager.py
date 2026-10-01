import json

from models.video_job import VideoJob
from core.video_job_manager import VideoJobManager


def test_video_job_persists_and_reloads(tmp_path):
    path = tmp_path / "video_jobs.json"
    manager = VideoJobManager(path)
    job = VideoJob(
        job_id="job-1",
        prompt="scene",
        reference_image="frame.png",
        comfy_prompt_id="prompt-1",
        status="running"
    )

    manager.create_job(job)
    reloaded = VideoJobManager(path).get_job("job-1")

    assert reloaded is not None
    assert reloaded.comfy_prompt_id == "prompt-1"
    assert reloaded.reference_image == "frame.png"


def test_video_job_persists_output_without_binary(tmp_path):
    path = tmp_path / "video_jobs.json"
    manager = VideoJobManager(path)
    manager.create_job(
        VideoJob(
            job_id="job-2",
            status="completed",
            progress=100,
            output_filename="video.mp4",
            output_subfolder="video",
            output_type="output"
        )
    )

    record = json.loads(path.read_text(encoding="utf-8"))[0]

    assert record["output_filename"] == "video.mp4"
    assert "video_base64" not in record


def test_malformed_video_job_file_raises(tmp_path):
    path = tmp_path / "video_jobs.json"
    path.write_text("{not-json", encoding="utf-8")

    try:
        VideoJobManager(path)
    except RuntimeError:
        return

    raise AssertionError("Expected malformed persistence to raise RuntimeError")
