from core.logger import Logger


class QueueManager:
    """
    Manages the execution queue.
    """

    def __init__(self):

        Logger.info("Initializing Queue Manager")

        self.queue = []

    def enqueue(
        self,
        job
    ) -> None:
        """
        Add a job to the queue.
        """

        self.queue.append(job)

        Logger.info(

            f"Job Queued: {job.id}"

        )

    def dequeue(self):
        """
        Remove and return the next job.
        """

        if self.queue:

            job = self.queue.pop(0)

            Logger.info(

                f"Job Dequeued: {job.id}"

            )

            return job

        Logger.warning(

            "Queue is empty."

        )

        return None

    def peek(self):
        """
        Return the next job without removing it.
        """

        if self.queue:

            return self.queue[0]

        return None

    def size(self) -> int:
        """
        Return queue size.
        """

        return len(self.queue)

    def is_empty(self) -> bool:
        """
        Check whether the queue is empty.
        """

        return len(self.queue) == 0

    def get_all(self) -> list:
        """
        Return all queued jobs.
        """

        return self.queue

    def clear(self) -> None:
        """
        Remove all jobs from the queue.
        """

        self.queue.clear()

        Logger.info(

            "Queue cleared."

        )