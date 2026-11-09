from core.provider_manager import ProviderManager
from core.model_manager import ModelManager
from core.job_manager import JobManager
from core.queue_manager import QueueManager
from core.worker_manager import WorkerManager
from core.progress_manager import ProgressManager
from core.workflows.manager import WorkflowManager
from core.video_job_manager import VideoJobManager
from core.video_worker import VideoWorker
from core.voice_profile_manager import VoiceProfileManager

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

        self.video_job_manager = VideoJobManager()

        self.voice_profile_manager = VoiceProfileManager()

        self.video_worker = VideoWorker(
            self.video_job_manager,
            self.provider_manager
        )