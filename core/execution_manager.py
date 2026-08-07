from core.logger import Logger
from core.server_context import server
from core.worker_manager import WorkerManager
from core.server_context import server



class ExecutionManager:

    @staticmethod
    def submit(job):

        Logger.info(f"Submitting Job : {job.id}")

        server.job_manager.create(job)

        server.queue_manager.enqueue(job)

        return job


    @staticmethod
    def execute_next():

        return WorkerManager.process(server)