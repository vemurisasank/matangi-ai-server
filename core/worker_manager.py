from core.logger import Logger


class WorkerManager:
    """
    Processes queued jobs.
    """

    @staticmethod
    def process(server):

        job = server.queue_manager.dequeue()

        if job is None:

            Logger.info("No jobs in queue.")

            return None

        Logger.info(

            f"Processing Job: {job.id}"

        )

        try:

            server.progress_manager.update(

                job,

                25

            )

            provider = server.provider_manager.get(

                job.provider

            )

            result = provider.generate(

                f"Test Job ({job.type})"

            )

            job.result = result

            server.progress_manager.update(

                job,

                100

            )

            server.progress_manager.complete(

                job

            )

            Logger.info(

                f"Job Completed: {job.id}"

            )

            return job

        except Exception as e:

            server.progress_manager.failed(

                job,

                str(e)

            )

            Logger.error(

                f"Job Failed: {job.id} | {e}"

            )

            return job