from core.provider_manager import ProviderManager
from core.model_manager import ModelManager
from core.job_manager import JobManager
from core.queue_manager import QueueManager
from core.worker_manager import WorkerManager
from core.progress_manager import ProgressManager
from core.workflows.manager import WorkflowManager

from config.settings import settings


class ServiceContainer:

    def __init__(self):

        self.settings = settings

        self.provider_manager = ProviderManager()

        self.model_manager = ModelManager()

        self.job_manager = JobManager()

        self.queue_manager = QueueManager()

        self.worker_manager = WorkerManager()

        self.progress_manager = ProgressManager()

        self.workflow_manager = WorkflowManager()