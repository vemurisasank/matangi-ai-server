import json
import os
import tempfile
from pathlib import Path
from threading import RLock

from core.logger import Logger
from config.paths import OUTPUTS
from models.job import Job


class JobManager:
    """
    Manages all jobs in the server.
    """

    def __init__(self, storage_path=None):

        Logger.info("Initializing Job Manager")

        self.storage_path = Path(
            storage_path or OUTPUTS / "image_jobs.json"
        )
        self._lock = RLock()
        self.jobs = {}
        self._load()

    @staticmethod
    def _serialize(job):
        return {
            "id": job.id,
            "type": job.type,
            "provider": job.provider,
            "model": job.model,
            "status": job.status,
            "progress": job.progress,
            "created_on": job.created_on,
            "started_on": job.started_on,
            "completed_on": job.completed_on,
            "error": job.error,
            "result": job.result
        }

    def _load(self):
        if not self.storage_path.exists():
            return

        try:
            with self.storage_path.open("r", encoding="utf-8") as file:
                records = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Unable to load persisted jobs from {self.storage_path}"
            ) from error

        if not isinstance(records, list):
            raise RuntimeError(
                f"Persisted jobs must be a list: {self.storage_path}"
            )

        for record in records:
            if not isinstance(record, dict) or "id" not in record:
                raise RuntimeError(
                    f"Invalid persisted job record: {self.storage_path}"
                )

            job = Job(
                id=record["id"],
                type=record.get("type", "image"),
                provider=record.get("provider", "comfyui"),
                model=record.get("model", "configured"),
                status=record.get("status", "queued"),
                progress=record.get("progress", 0),
                created_on=record.get("created_on", ""),
                started_on=record.get("started_on", ""),
                completed_on=record.get("completed_on", "")
            )
            job.error = record.get("error", "")
            job.result = record.get("result")
            self.jobs[job.id] = job

    def _save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        records = [
            self._serialize(job)
            for job in self.jobs.values()
        ]

        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.storage_path.parent,
                prefix=f".{self.storage_path.name}.",
                suffix=".tmp",
                delete=False
            ) as file:
                temporary_path = Path(file.name)
                json.dump(records, file, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_path, self.storage_path)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    def persist(self, job: Job) -> None:
        with self._lock:
            self.jobs[job.id] = job
            self._save()

    def create(
        self,
        job: Job
    ) -> Job:
        """
        Create a new job.
        """

        self.persist(job)

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
            self.persist(job)

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
            with self._lock:
                self._save()

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
        with self._lock:
            self._save()

        Logger.info(

            "All jobs cleared."

        )