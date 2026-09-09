from datetime import datetime
import uuid

from fastapi import APIRouter
from fastapi import BackgroundTasks

from api.schemas.image_schema import ImageRequest

from engines.image_engine import ImageEngine

from core.server_context import server
from core.response_manager import ResponseManager

from models.job import Job

router = APIRouter()


@router.post("/image")

def generate_image(request: ImageRequest):
    try:
        result = ImageEngine.generate(request)

        return ResponseManager.success(

            result,

            "Image Generated Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )


def _run_image_job(job_id, request):
    job = server.job_manager.get(job_id)

    if job is None:
        return

    job.status = "running"
    job.started_on = datetime.now().isoformat()

    try:
        job.result = ImageEngine.generate(request)
        job.status = "completed"
        job.progress = 100
        job.completed_on = datetime.now().isoformat()

    except Exception as error:
        job.status = "failed"
        job.error = str(error)
        job.completed_on = datetime.now().isoformat()


@router.post("/image/jobs")
def create_image_job(
    request: ImageRequest,
    background_tasks: BackgroundTasks
):
    job = Job(
        id=str(uuid.uuid4()),
        type="image",
        provider="comfyui",
        model=request.model or "configured",
        status="queued",
        progress=0
    )

    server.job_manager.create(job)
    background_tasks.add_task(
        _run_image_job,
        job.id,
        request
    )

    return ResponseManager.success(
        {
            "job_id": job.id,
            "status": job.status
        },
        "Image Job Created"
    )


@router.get("/image/jobs/{job_id}")
def get_image_job(job_id: str):
    job = server.job_manager.get(job_id)

    if job is None:
        return ResponseManager.failure(
            "Image job not found."
        )

    data = {
        "job_id": job.id,
        "status": job.status
    }

    if job.status == "completed":
        data["result"] = job.result

    if job.status == "failed":
        data["error"] = job.error

    return ResponseManager.success(
        data,
        "Image Job Status Retrieved"
    )