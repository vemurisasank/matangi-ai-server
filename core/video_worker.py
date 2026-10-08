import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from core.logger import Logger
from models.video_job import VideoJob


COMFY_INPUT_DIR = Path("/workspace/ComfyUI/input")


class VideoWorker:

    def __init__(self, job_manager, provider_manager):
        self.job_manager = job_manager
        self.provider_manager = provider_manager
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lifecycle_lock = threading.RLock()

    def start(self):
        with self._lifecycle_lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="matangi-video-worker",
                daemon=True
            )
            self._thread.start()

    def stop(self):
        with self._lifecycle_lock:
            self._stop_event.set()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=5)
        with self._lifecycle_lock:
            self._thread = None

    def _run(self):
        self._recover_jobs()
        while not self._stop_event.is_set():
            job = self.job_manager.claim_next_queued()
            if job is not None:
                self._execute(job)
                continue
            self._stop_event.wait(1)

    def _recover_jobs(self):
        now = _now()
        for job in self.job_manager.list_jobs():
            if job.status == "running":
                if job.stage == "h3" and not (
                    job.h3_prompt_id or job.comfy_prompt_id
                ):
                    self.job_manager.update_job(
                        job.job_id,
                        status="failed",
                        completed_at=now,
                        error=(
                            "Video job was running without a ComfyUI "
                            "prompt_id during recovery."
                        )
                    )
                else:
                    self._execute(job)

    def _execute(self, job: VideoJob):
        try:
            provider = self.provider_manager.get(job.provider)
            if job.stage == "h3":
                h3_prompt_id = job.h3_prompt_id or job.comfy_prompt_id
                if h3_prompt_id and not job.h3_prompt_id:
                    self.job_manager.update_job(
                        job.job_id,
                        h3_prompt_id=h3_prompt_id,
                        stage="h3"
                    )
                    job.h3_prompt_id = h3_prompt_id
                if not h3_prompt_id:
                    if not job.reference_images and not job.reference_image:
                        raise ValueError(
                            "reference_image or reference_images is required for H3."
                        )
                    h3_prompt_id = provider.submit_video(
                        prompt=job.prompt,
                        duration=job.duration,
                        fps=job.fps,
                        width=job.width,
                        height=job.height,
                        reference_image=job.reference_image,
                        reference_images=job.reference_images,
                        seed=job.seed,
                        model=job.model
                    )
                    self.job_manager.update_job(
                        job.job_id,
                        started_at=job.started_at or _now(),
                        comfy_prompt_id=h3_prompt_id,
                        h3_prompt_id=h3_prompt_id,
                        stage="h3"
                    )
                    job.h3_prompt_id = h3_prompt_id
                    job.comfy_prompt_id = h3_prompt_id

                result = self._wait_for_result(provider, h3_prompt_id)
                output = provider.find_video_output(result)
                if output is None:
                    raise RuntimeError(
                        "H3 video output was not found in ComfyUI history."
                    )
                output_path = _output_path(output)
                if output_path is None:
                    raise RuntimeError("H3 video output path is invalid.")
                self.job_manager.update_job(
                    job.job_id,
                    status="completed",
                    stage="completed",
                    progress=100,
                    completed_at=_now(),
                    output_filename=output["filename"],
                    output_subfolder=output.get("subfolder", ""),
                    output_type=output.get("type", "output"),
                    output_path=output_path
                )
                return

            if job.stage != "seedvr2":
                raise RuntimeError(f"Unknown video job stage: {job.stage}")

            if not job.intermediate_video_path:
                raise RuntimeError("SeedVR2 input video path is missing.")

            seedvr2_prompt_id = job.seedvr2_prompt_id
            if not seedvr2_prompt_id:
                seedvr2_prompt_id = provider.submit_seedvr2_video(
                    Path(job.intermediate_video_path).name
                )
                self.job_manager.update_job(
                    job.job_id,
                    comfy_prompt_id=seedvr2_prompt_id,
                    seedvr2_prompt_id=seedvr2_prompt_id,
                    stage="seedvr2"
                )
                job.seedvr2_prompt_id = seedvr2_prompt_id
                job.comfy_prompt_id = seedvr2_prompt_id

            result = self._wait_for_result(provider, seedvr2_prompt_id)
            output = provider.find_video_output(result)
            if output is None:
                raise RuntimeError(
                    "SeedVR2 video output was not found in ComfyUI history."
                )

            output_path = _output_path(output)
            self.job_manager.update_job(
                job.job_id,
                status="completed",
                stage="completed",
                progress=100,
                completed_at=_now(),
                output_filename=output["filename"],
                output_subfolder=output.get("subfolder", ""),
                output_type=output.get("type", "output"),
                output_path=output_path
            )
        except Exception as error:
            Logger.error(f"Video job {job.job_id} failed: {error}")
            self.job_manager.update_job(
                job.job_id,
                status="failed",
                completed_at=_now(),
                error=str(error)
            )

    def _wait_for_result(self, provider, prompt_id):
        while not self._stop_event.is_set():
            history = provider.get_video_history(prompt_id)
            if history is None:
                self._stop_event.wait(1)
                continue
            status = history.get("status", {})
            status_string = status.get("status_str")
            if status_string in {"error", "failed"}:
                raise RuntimeError(
                    f"ComfyUI execution failed: {status.get('messages', status)}"
                )
            if status.get("completed") or status_string == "success":
                return history
            self._stop_event.wait(1)
        raise RuntimeError("Video worker stopped before job completion.")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _output_path(output):
    root = Path("/workspace/ComfyUI/output").resolve()
    path = (
        root
        / output.get("subfolder", "")
        / output["filename"]
    ).resolve()
    if root not in path.parents:
        return None
    return str(path)


def _stage_intermediate_video(source_path, job_id, source_filename):
    source = Path(source_path).resolve()
    output_root = Path("/workspace/ComfyUI/output").resolve()
    if output_root not in source.parents or not source.is_file():
        raise RuntimeError(f"H3 intermediate video path is invalid: {source}")

    destination = COMFY_INPUT_DIR / f"matangi_h3_{job_id}_{Path(source_filename).name}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file():
        shutil.copy2(source, destination)
    return str(destination)
