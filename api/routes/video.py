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
    if request.reference_images and request.ref_images is not None:
        return ResponseManager.failure(
            "Provide either reference_images or ref_images, not both."
        )

    reference_images = request.reference_images
    if request.ref_images is not None:
        try:
            reference_images = _ordered_reference_images(request.ref_images)
        except ValueError as error:
            return ResponseManager.failure(str(error))

    if len(reference_images) > 9:
        return ResponseManager.failure(
            "MiniMax H3 supports at most 9 reference images."
        )
    if request.reference_metadata is not None:
        if not reference_images:
            return ResponseManager.failure(
                "reference_metadata requires reference_images."
            )
        if len(request.reference_metadata) != len(reference_images):
            return ResponseManager.failure(
                "reference_metadata must contain one entry per reference image."
            )
    if not reference_images and not request.reference_image:
        return ResponseManager.failure(
            "reference_image or reference_images is required for MiniMax H3."
        )

    prompt = request.prompt
    reference_metadata = None
    if request.reference_metadata is not None:
        reference_metadata = [
            (
                metadata.model_dump()
                if hasattr(metadata, "model_dump")
                else metadata.dict()
            )
            for metadata in request.reference_metadata
        ]
        prompt = _append_reference_assignments(
            prompt,
            reference_images,
            reference_metadata
        )

    job = VideoJob(
        job_id=str(uuid.uuid4()),
        created_at=_now(),
        prompt=prompt,
        duration=request.duration,
        fps=request.fps,
        width=request.width,
        height=request.height,
        reference_image=request.reference_image,
        reference_images=reference_images,
        reference_metadata=reference_metadata,
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


def _ordered_reference_images(ref_images):
    expected = set()
    ordered = []
    for key, filename in ref_images.items():
        prefix = "ref_image_"
        if not key.startswith(prefix):
            raise ValueError(
                "ref_images keys must be ref_image_0 through ref_image_8."
            )
        try:
            index = int(key[len(prefix):])
        except ValueError as error:
            raise ValueError(
                "ref_images keys must be ref_image_0 through ref_image_8."
            ) from error
        if index < 0 or index > 8 or index in expected:
            raise ValueError(
                "ref_images keys must be unique values from ref_image_0 "
                "through ref_image_8."
            )
        expected.add(index)

    if expected != set(range(len(expected))):
        raise ValueError(
            "ref_images keys must be contiguous starting at ref_image_0."
        )

    for index in range(len(expected)):
        ordered.append(ref_images[f"ref_image_{index}"])
    return ordered


def _append_reference_assignments(prompt, reference_images, metadata):
    lines = [
        "",
        "============================================================",
        "REFERENCE IMAGE ASSIGNMENTS",
        "============================================================",
        ""
    ]
    for index, (filename, assignment) in enumerate(
        zip(reference_images, metadata),
        start=1
    ):
        lines.extend([
            f"Reference {index}",
            f"Type: {assignment['type']}",
            f"Asset: {assignment['name']}",
            f"Uploaded file: {filename}",
            f"H3 slot: ref_images.ref_image_{index - 1}",
            ""
        ])
    lines.extend([
        "REFERENCE USAGE:",
        "Use each supplied reference according to its assigned type and asset name.",
        "Maintain the identity and visual characteristics of each referenced character.",
        "Maintain the appearance and design of each referenced costume.",
        "Maintain the visual identity of the referenced environment.",
        "Maintain the identity and appearance of the referenced props.",
        "Do not confuse one reference with another.",
        "Only use the supplied references relevant to this scene."
    ])
    return f"{prompt}\n" + "\n".join(lines)