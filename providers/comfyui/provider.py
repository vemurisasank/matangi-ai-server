import base64
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
        seed,
        reference_images=None
    ):

        if reference_images is None:
            reference_images = []

        from core.workflows.manager import WorkflowManager

        workflow = WorkflowManager.build(
            settings.IMAGE_WORKFLOW,
            {
                "prompt": prompt,
                "width": width,
                "height": height,
                "seed": seed,
                "reference_images": reference_images
            }
        )

        prompt_id = self.client.queue_prompt(
            workflow
        )

        result = self.monitor.wait(prompt_id)

        image = ComfyUIImageParser.parse(
            result
        )

        if image is None:

            return {
                "success": False,
                "provider": "ComfyUI",
                "message": "Generated image was not found."
            }

        image_bytes = self.client.get_image(
            filename=image["filename"],
            subfolder=image.get("subfolder", ""),
            image_type=image.get("type", "output")
        )

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        return {
            "success": True,
            "provider": "ComfyUI",
            "image": image,
            "image_base64": image_base64
        }

        
    def generate_video(
        self,
        prompt,
        duration=5,
        fps=25,
        width=1024,
        height=576,
        reference_image=None,
        seed=0
    ):

        if not reference_image:
            raise ValueError(
                "reference_image is required for LTX-2.3 image-to-video"
            )

        from providers.comfyui.video_workflow_loader import (
            LTXVideoWorkflowLoader
        )

        workflow = LTXVideoWorkflowLoader.load(
            prompt=prompt,
            reference_image=reference_image,
            width=width,
            height=height,
            duration=duration,
            fps=fps,
            seed=seed
        )

        prompt_id = self.client.queue_prompt(
            workflow
        )

        result = self.monitor.wait(
            prompt_id
        )

        outputs = result.get("outputs", {})

        for node in outputs.values():

            if "images" in node:

                for item in node["images"]:

                    if item.get("type") == "output":

                        video_bytes = self.client.get_output(

                            filename=item["filename"],

                            subfolder=item.get("subfolder", ""),

                            output_type=item.get("type", "output")

                        )

                        video_base64 = base64.b64encode(
                            video_bytes
                        ).decode("utf-8")

                        return {
                            "success": True,
                            "provider": "ComfyUI",
                            "video": item,
                            "video_base64": video_base64
                        }

        return {
            "success": False,
            "provider": "ComfyUI",
            "error": "Video output was not found"
        }


    def generate_voice(
        self,
        text,
        voice="Ryan",
        language="Auto",
        instruct="",
        seed=-1
    ):

        import json

        workflow_path = (
            "/workspace/matangi-ai-server/"
            "workflows/qwen3_tts_custom_voice_api.json"
        )

        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        qwen_node = workflow["61"]["inputs"]

        qwen_node["text"] = text
        qwen_node["speaker"] = voice
        qwen_node["language"] = language
        qwen_node["instruct"] = instruct
        qwen_node["seed"] = seed

        prompt_id = self.client.queue_prompt(workflow)

        result = self.monitor.wait(prompt_id)

        outputs = result.get("outputs", {})

        for node in outputs.values():

            if "audio" in node:

                for item in node["audio"]:

                    if item.get("type") == "output":

                        return {
                            "success": True,
                            "provider": "Qwen3-TTS",
                            "audio": item
                        }

        return {
            "success": False,
            "provider": "Qwen3-TTS",
            "error": "Voice output was not found"
        }
