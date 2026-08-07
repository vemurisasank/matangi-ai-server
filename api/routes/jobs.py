import uuid

from fastapi import APIRouter

from core.server_context import server

from core.response_manager import ResponseManager

from models.job import Job

from core.execution_manager import ExecutionManager

from core.execution_manager import ExecutionManager

router = APIRouter()


@router.post("/jobs")

def create_job():

    job = Job(

        id=str(uuid.uuid4()),

        type="image",

        provider="ollama",

        model="flux",

        status="Pending",

        progress=0

    )

    ExecutionManager.submit(job)

    return ResponseManager.success(

        {

            "job_id": job.id

        },

        "Job Created"

    )


@router.get("/jobs")

def get_jobs():

    jobs = []

    for job in server.job_manager.get_all():

        jobs.append(job.__dict__)

    return ResponseManager.success(

        jobs,

        "Jobs Retrieved"

    )
@router.post("/jobs/execute")

def execute_job():

    job = ExecutionManager.execute_next()

    if job is None:

        return ResponseManager.failure(

            "No Jobs Available"

        )

    return ResponseManager.success(

        job.__dict__,

        "Job Executed Successfully"

    )