import base64

from providers.comfyui.client import ComfyUIClient
from config.settings import settings
from providers.comfyui.job_monitor import ComfyUIJobMonitor
from providers.comfyui.image_parser import ComfyUIImageParser
from providers.comfyui.three_d_parser import ComfyUI3DParser
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
        reference_images=None,
        steps=20,
        cfg=4.0,
        sampler="euler",
        scheduler="simple",
        model=None
    ):

        if reference_images is None:
            reference_images = []

        if model == "qwen-image-edit-2511":

            from providers.comfyui.qwen_image_workflow_loader import (
                QwenImageWorkflowLoader
            )

            workflow = QwenImageWorkflowLoader.build(
                prompt=prompt,
                width=width,
                height=height,
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler=sampler,
                scheduler=scheduler,
                reference_images=reference_images
            )

        else:

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

        response = {
            "success": True,
            "provider": "ComfyUI",
            "image": image,
            "image_base64": image_base64
        }

        if model == "qwen-image-edit-2511":
            response["model"] = model

        return response


    def generate_3d(
        self,
        image,
        asset_id="matangi_asset",
        resolution=3072,
        batch_size=1,
        seed=-1,
        steps=30,
        cfg=5.0,
        octree_resolution=256,
        threshold=0.6
    ):

        from providers.comfyui.three_d_workflow_loader import (
            ThreeDWorkflowLoader
        )

        safe_asset_id = "".join(
            character
            if character.isalnum() or character in ("_", "-")
            else "_"
            for character in asset_id
        )

        if not safe_asset_id:
            safe_asset_id = "matangi_asset"

        safe_image = image.split("/")[-1].split("\\")[-1]

        workflow = ThreeDWorkflowLoader.build(
            image=safe_image,
            resolution=resolution,
            batch_size=batch_size,
            seed=seed,
            steps=steps,
            cfg=cfg,
            octree_resolution=octree_resolution,
            threshold=threshold,
            filename_prefix=f"matangi_3d/{safe_asset_id}"
        )

        prompt_id = self.client.queue_prompt(
            workflow
        )

        result = self.monitor.wait(
            prompt_id
        )

        output = ComfyUI3DParser.parse(
            result
        )

        if output is None:

            return {
                "success": False,
                "provider": "ComfyUI",
                "asset_id": safe_asset_id,
                "error": "3D GLB output was not found.",
                "prompt_id": prompt_id
            }

        glb_bytes = self.client.get_output(
            filename=output["filename"],
            subfolder=output.get("subfolder", ""),
            output_type=output.get("type", "output")
        )

        import os

        output_directory = (
            "/workspace/matangi-ai-server/"
            "outputs/3d"
        )

        os.makedirs(
            output_directory,
            exist_ok=True
        )

        output_filename = (
            f"{safe_asset_id}.glb"
        )

        output_path = os.path.join(
            output_directory,
            output_filename
        )

        with open(
            output_path,
            "wb"
        ) as file:

            file.write(
                glb_bytes
            )

        return {
            "success": True,
            "provider": "ComfyUI",
            "asset_id": safe_asset_id,
            "format": "glb",
            "file": output_path,
            "filename": output_filename,
            "size_bytes": len(glb_bytes),
            "prompt_id": prompt_id,
            "comfyui_output": output
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

        with open(
            workflow_path,
            "r",
            encoding="utf-8"
        ) as file:

            workflow = json.load(file)

        qwen_node = workflow["61"]["inputs"]

        qwen_node["text"] = text
        qwen_node["speaker"] = voice
        qwen_node["language"] = language
        qwen_node["instruct"] = instruct
        qwen_node["seed"] = seed

        prompt_id = self.client.queue_prompt(
            workflow
        )

        result = self.monitor.wait(
            prompt_id
        )

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
