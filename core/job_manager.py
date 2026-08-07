from core.logger import Logger
from models.job import Job


class JobManager:
    """
    Manages all jobs in the server.
    """

    def __init__(self):

        Logger.info("Initializing Job Manager")

        self.jobs = {}

    def create(
        self,
        job: Job
    ) -> Job:
        """
        Create a new job.
        """

        self.jobs[job.id] = job

        Logger.info(

            f"Job Created: {job.id}"

        )

        return job

    def get(
        self,
        job_id: str
    ) -> Job | None:
        """
        Get a job by ID.
        """

        return self.jobs.get(job_id)

    def get_all(self) -> list:
        """
        Get all jobs.
        """

        return list(

            self.jobs.values()

        )

    def update(
        self,
        job_id: str,
        status: str,
        progress: int
    ) -> bool:
        """
        Update a job.
        """

        job = self.jobs.get(job_id)

        if job:

            job.status = status

            job.progress = progress

            Logger.info(

                f"Job Updated: {job_id}"

            )

            return True

        Logger.warning(

            f"Job '{job_id}' not found."

        )

        return False

    def remove(
        self,
        job_id: str
    ) -> bool:
        """
        Remove a job.
        """

        if job_id in self.jobs:

            del self.jobs[job_id]

            Logger.info(

                f"Job Removed: {job_id}"

            )

            return True

        Logger.warning(

            f"Job '{job_id}' not found."

        )

        return False

    def list(self) -> list:
        """
        List all job IDs.
        """

        return list(

            self.jobs.keys()

        )

    def exists(
        self,
        job_id: str
    ) -> bool:
        """
        Check whether a job exists.
        """

        return job_id in self.jobs

    def clear(self) -> None:
        """
        Remove all jobs.
        """

        self.jobs.clear()

        Logger.info(

            "All jobs cleared."

        )