from pathlib import Path

from PIL import Image

import core.video_worker as video_worker
from core.video_frames import VideoFrameResult, VideoFrameExtractionError
from core.video_job_manager import VideoJobManager
from models.video_job import VideoJob


OUTPUT_ROOT = Path("/workspace/ComfyUI/output")


class FakeProvider:
    def __init__(self, output_path):
        self.output_path = output_path
        self.submitted = False

    def submit_video(self, **kwargs):
        self.submitted = True
        return "h3-prompt"

    def get_video_history(self, prompt_id):
        return {
            "status": {"completed": True, "status_str": "success"},
            "outputs": {
                "20": {
                    "videos": [{
                        "filename": self.output_path.name,
                        "subfolder": "video",
                        "type": "output"
                    }]
                }
            }
        }

    def find_video_output(self, result):
        return result["outputs"]["20"]["videos"][0]


class FakeProviderManager:
    def __init__(self, provider):
        self.provider = provider

    def get(self, provider_name):
        return self.provider


def _job_manager(tmp_path):
    return VideoJobManager(tmp_path / "video_jobs.json")


def _source_video():
    source = OUTPUT_ROOT / "video" / ".test_video_worker.mp4"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"mock video")
    return source


def test_worker_persists_successful_last_frame_metadata(monkeypatch, tmp_path):
    source = _source_video()
    manager = _job_manager(tmp_path)
    job = VideoJob(
        job_id="worker-frame-success",
        status="running",
        stage="h3",
        h3_prompt_id="h3-prompt",
        comfy_prompt_id="h3-prompt",
        project="project/one",
        scene_id="scene:one"
    )
    manager.create_job(job)
    provider = FakeProvider(source)
    worker = video_worker.VideoWorker(
        manager,
        FakeProviderManager(provider)
    )

    def fake_extract(source_video, output_path):
        Image.new("RGB", (1024, 704)).save(output_path, format="PNG")
        return VideoFrameResult(
            output_path=str(output_path),
            width=1024,
            height=704,
            frame_index=446,
            frame_count=447
        )

    monkeypatch.setattr(video_worker, "extract_last_frame", fake_extract)
    try:
        worker._execute(job)
        persisted = manager.get_job(job.job_id)
        assert persisted.status == "completed"
        assert persisted.output_path == str(source.resolve())
        assert persisted.last_frame_status == "ready"
        assert persisted.last_frame_path is not None
        assert Path(persisted.last_frame_path).is_file()
        assert persisted.last_frame_filename == "last_frame.png"
        assert persisted.last_frame_width == 1024
        assert persisted.last_frame_height == 704
        assert persisted.last_frame_error is None
        assert "project_one" in persisted.last_frame_path
        assert "scene_one" in persisted.last_frame_path
    finally:
        source.unlink(missing_ok=True)
        if persisted.last_frame_path:
            Path(persisted.last_frame_path).unlink(missing_ok=True)


def test_worker_preserves_video_when_last_frame_extraction_fails(
    monkeypatch,
    tmp_path
):
    source = _source_video()
    manager = _job_manager(tmp_path)
    job = VideoJob(
        job_id="worker-frame-failure",
        status="running",
        stage="h3",
        h3_prompt_id="h3-prompt",
        comfy_prompt_id="h3-prompt"
    )
    manager.create_job(job)
    provider = FakeProvider(source)
    worker = video_worker.VideoWorker(
        manager,
        FakeProviderManager(provider)
    )
    monkeypatch.setattr(
        video_worker,
        "extract_last_frame",
        lambda source_video, output_path: (_ for _ in ()).throw(
            VideoFrameExtractionError("frame decode failed")
        )
    )
    try:
        worker._execute(job)
        persisted = manager.get_job(job.job_id)
        assert persisted.status == "completed"
        assert persisted.output_path == str(source.resolve())
        assert persisted.output_filename == source.name
        assert persisted.last_frame_status == "failed"
        assert persisted.last_frame_error == "frame decode failed"
        assert persisted.last_frame_path is None
    finally:
        source.unlink(missing_ok=True)


def test_worker_reuses_valid_existing_last_frame(monkeypatch, tmp_path):
    source = _source_video()
    manager = _job_manager(tmp_path)
    frame_path = video_worker.CONTINUITY_OUTPUT_DIR / "reuse" / "scene" / "job" / "last_frame.png"
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (640, 352)).save(frame_path, format="PNG")
    job = VideoJob(
        job_id="worker-frame-reuse",
        status="running",
        stage="h3",
        h3_prompt_id="h3-prompt",
        comfy_prompt_id="h3-prompt",
        last_frame_path=str(frame_path),
        last_frame_filename="last_frame.png",
        last_frame_width=640,
        last_frame_height=352,
        last_frame_status="ready"
    )
    manager.create_job(job)
    provider = FakeProvider(source)
    worker = video_worker.VideoWorker(
        manager,
        FakeProviderManager(provider)
    )
    extract_calls = []
    monkeypatch.setattr(
        video_worker,
        "extract_last_frame",
        lambda source_video, output_path: extract_calls.append(output_path)
    )
    try:
        worker._execute(job)
        persisted = manager.get_job(job.job_id)
        assert persisted.last_frame_status == "ready"
        assert persisted.last_frame_path == str(frame_path.resolve())
        assert extract_calls == []
    finally:
        source.unlink(missing_ok=True)
        frame_path.unlink(missing_ok=True)

