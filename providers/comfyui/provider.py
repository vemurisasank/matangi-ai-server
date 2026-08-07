from providers.comfyui.client import ComfyUIClient
from config.settings import settings
from providers.comfyui.workflow_loader import WorkflowLoader
from providers.comfyui.job_monitor import ComfyUIJobMonitor
from providers.comfyui.image_parser import ComfyUIImageParser
from providers.base.provider import BaseProvider

class ComfyUIProvider(BaseProvider):

    def __init__(self):

        super().__init__("ComfyUI")

        self.client = ComfyUIClient()

        self.monitor = ComfyUIJobMonitor()

    def generate(

        self,

        prompt,

        width,

        height,

        seed

    ):

        from core.workflows.manager import WorkflowManager

        workflow = WorkflowManager.build(

            settings.IMAGE_WORKFLOW,

            {

                "prompt": prompt,

                "width": width,

                "height": height,

                "seed": seed

            }

        )

        prompt_id = self.client.queue_prompt(

            workflow

        )

        result = self.monitor.wait(prompt_id)
        
        image = ComfyUIImageParser.parse(

            result

        )

        return {

            "success": True,

            "provider": "ComfyUI",

            "image": image

        }

        