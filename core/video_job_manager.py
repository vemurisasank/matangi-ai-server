import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from config.paths import OUTPUTS
from core.logger import Logger
from models.video_job import VideoJob


class VideoJobManager:

    def __init__(self, storage_path=None):
        self.storage_path = Path(
            storage_path or OUTPUTS / "video_jobs.json"
        )
        self._lock = RLock()
        self.jobs: dict[str, VideoJob] = {}
        self._load()

    @staticmethod
    def _serialize(job: VideoJob) -> dict:
        return {
            key: getattr(job, key)
            for key in VideoJob.__dataclass_fields__
        }

    def _load(self):
        if not self.storage_path.exists():
            return

        try:
            with self.storage_path.open("r", encoding="utf-8") as file:
                records = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Unable to load persisted video jobs from {self.storage_path}"
            ) from error

        if not isinstance(records, list):
            raise RuntimeError(
                f"Persisted video jobs must be a list: {self.storage_path}"
            )

        for record in records:
            if not isinstance(record, dict) or "job_id" not in record:
                raise RuntimeError(
                    f"Invalid persisted video job record: {self.storage_path}"
                )
            fields = {
                key: record[key]
                for key in VideoJob.__dataclass_fields__
                if key in record
            }
            self.jobs[record["job_id"]] = VideoJob(**fields)

    def _save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        records = [self._serialize(job) for job in self.jobs.values()]
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

    def create_job(self, job: VideoJob) -> VideoJob:
        with self._lock:
            if job.job_id in self.jobs:
                raise ValueError(f"Video job '{job.job_id}' already exists.")
            self.jobs[job.job_id] = job
            self._save()
        Logger.info(f"Video Job Created: {job.job_id}")
        return job

    def get_job(self, job_id: str) -> VideoJob | None:
        with self._lock:
            return self.jobs.get(job_id)

    def update_job(self, job_id: str, **changes) -> VideoJob:
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise KeyError(f"Video job '{job_id}' not found.")
            for key, value in changes.items():
                if key not in VideoJob.__dataclass_fields__:
                    raise ValueError(f"Unknown video job field: {key}")
                setattr(job, key, value)
            self._save()
            return job

    def list_jobs(self, status: str | None = None) -> list[VideoJob]:
        with self._lock:
            jobs = list(self.jobs.values())
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        return sorted(jobs, key=lambda job: job.created_at)

    def claim_next_queued(self) -> VideoJob | None:
        with self._lock:
            queued = [
                job for job in self.jobs.values()
                if job.status == "queued"
            ]
            if not queued:
                return None
            job = min(queued, key=lambda item: item.created_at)
            job.status = "running"
            job.started_at = datetime.now(timezone.utc).isoformat()
            self._save()
            return job
