from core.logger import Logger


class ProgressManager:
    """
    Manages job progress and status.
    """

    @staticmethod
    def update(
        job,
        progress: int
    ) -> None:
        """
        Update job progress.
        """

        job.progress = progress

        Logger.info(

            f"Job {job.id}: {progress}%"

        )

    @staticmethod
    def complete(job) -> None:
        """
        Mark a job as completed.
        """

        job.progress = 100

        job.status = "Completed"

        Logger.info(

            f"Job Completed: {job.id}"

        )

    @staticmethod
    def failed(
        job,
        error: str
    ) -> None:
        """
        Mark a job as failed.
        """

        job.status = "Failed"

        job.error = error

        Logger.error(

            f"Job Failed: {job.id} | {error}"

        )

    @staticmethod
    def reset(job) -> None:
        """
        Reset a job.
        """

        job.progress = 0

        job.status = "Pending"

        job.error = None

        Logger.info(

            f"Job Reset: {job.id}"

        )