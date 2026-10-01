from pathlib import Path
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response

from api.schemas.video_schema import AsyncVideoRequest, VideoRequest

from engines.video_engine import VideoEngine

from core.response_manager import ResponseManager
from core.server_context import server
from models.video_job import VideoJob


router = APIRouter()


@router.post("/video")

def generate_video(request: VideoRequest):

    try:

        result = VideoEngine.generate(request)

        return ResponseManager.success(

            result,

            "Video Generated Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )


@router.post("/video/jobs")
def create_video_job(request: AsyncVideoRequest):
    if request.model != "minimax-h3":
        return ResponseManager.failure(
            "POST /video/jobs requires model='minimax-h3'."
        )
    if not request.reference_image:
        return ResponseManager.failure(
            "reference_image is required for MiniMax H3."
        )

    job = VideoJob(
        job_id=str(uuid.uuid4()),
        created_at=_now(),
        prompt=request.prompt,
        duration=request.duration,
        fps=request.fps,
        width=request.width,
        height=request.height,
        reference_image=request.reference_image,
        seed=request.seed,
        scene_id=request.scene_id,
        project=request.project
    )
    server.video_job_manager.create_job(job)

    return ResponseManager.success(
        {"job_id": job.job_id, "status": job.status},
        "Video Job Created"
    )


@router.get("/video/jobs/{job_id}")
def get_video_job(job_id: str):
    job = server.video_job_manager.get_job(job_id)
    if job is None:
        return ResponseManager.failure("Video job not found.")

    data = {
        "job_id": job.job_id,
        "status": job.status,
        "model": job.model,
        "progress": job.progress
    }
    if job.comfy_prompt_id:
        data["prompt_id"] = job.comfy_prompt_id
    if job.status == "completed":
        data["output"] = {
            "filename": job.output_filename,
            "subfolder": job.output_subfolder,
            "type": job.output_type
        }
    if job.status == "failed":
        data["error"] = job.error
    return ResponseManager.success(data, "Video Job Status Retrieved")


@router.get("/video/jobs/{job_id}/download")
def download_video_job(job_id: str):
    job = server.video_job_manager.get_job(job_id)
    if job is None:
        return ResponseManager.failure("Video job not found.")
    if job.status != "completed":
        return ResponseManager.failure("Video job is not completed.")
    if not job.output_filename:
        return ResponseManager.failure("Video output metadata is missing.")

    output_path = Path(job.output_path).resolve() if job.output_path else None
    output_root = Path("/workspace/ComfyUI/output").resolve()
    if output_path is not None and output_root not in output_path.parents:
        return ResponseManager.failure(
            "Persisted video output path is outside the ComfyUI output directory."
        )
    if output_path is not None and output_path.is_file():
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=job.output_filename
        )

    try:
        provider = server.provider_manager.get(job.provider)
        content = provider.client.get_output(
            filename=job.output_filename,
            subfolder=job.output_subfolder,
            output_type=job.output_type
        )
        return Response(content, media_type="video/mp4")
    except Exception as error:
        return ResponseManager.failure(
            f"Video output is unavailable: {error}"
        )


def _now():
    return datetime.now(timezone.utc).isoformat()