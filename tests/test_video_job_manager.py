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
    assert reloaded.reference_images == []


def test_video_job_persists_ordered_reference_images(tmp_path):
    path = tmp_path / "video_jobs.json"
    manager = VideoJobManager(path)
    manager.create_job(
        VideoJob(
            job_id="job-r2v",
            reference_images=["one.png", "two.png", "three.png"]
        )
    )

    reloaded = VideoJobManager(path).get_job("job-r2v")

    assert reloaded is not None
    assert reloaded.reference_images == ["one.png", "two.png", "three.png"]


def test_video_job_persists_reference_metadata(tmp_path):
    path = tmp_path / "video_jobs.json"
    manager = VideoJobManager(path)
    metadata = [{"type": "CHARACTER", "name": "Ganesha"}]
    manager.create_job(
        VideoJob(
            job_id="job-metadata",
            reference_images=["ganesha.png"],
            reference_metadata=metadata
        )
    )

    reloaded = VideoJobManager(path).get_job("job-metadata")

    assert reloaded is not None
    assert reloaded.reference_metadata == metadata


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


def test_video_job_persists_last_frame_metadata(tmp_path):
    path = tmp_path / "video_jobs.json"
    manager = VideoJobManager(path)
    manager.create_job(
        VideoJob(
            job_id="job-frame",
            last_frame_path="/outputs/continuity/job-frame/last_frame.png",
            last_frame_filename="last_frame.png",
            last_frame_width=1024,
            last_frame_height=704,
            last_frame_status="ready"
        )
    )

    reloaded = VideoJobManager(path).get_job("job-frame")

    assert reloaded is not None
    assert reloaded.last_frame_path.endswith("last_frame.png")
    assert reloaded.last_frame_filename == "last_frame.png"
    assert reloaded.last_frame_width == 1024
    assert reloaded.last_frame_height == 704
    assert reloaded.last_frame_status == "ready"
    assert reloaded.last_frame_error is None


def test_legacy_video_job_without_last_frame_fields_loads(tmp_path):
    path = tmp_path / "video_jobs.json"
    path.write_text(
        '[{"job_id": "legacy-job", "status": "completed"}]',
        encoding="utf-8"
    )

    job = VideoJobManager(path).get_job("legacy-job")

    assert job is not None
    assert job.last_frame_path is None
    assert job.last_frame_filename is None
    assert job.last_frame_width is None
    assert job.last_frame_height is None
    assert job.last_frame_status == "not_requested"
    assert job.last_frame_error is None


def test_malformed_video_job_file_raises(tmp_path):
    path = tmp_path / "video_jobs.json"
    path.write_text("{not-json", encoding="utf-8")

    try:
        VideoJobManager(path)
    except RuntimeError:
        return

    raise AssertionError("Expected malformed persistence to raise RuntimeError")
