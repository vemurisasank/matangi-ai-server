import json
from pathlib import Path


class WorkflowLoader:

    WORKFLOW_DIR = Path(__file__).resolve().parents[2] / "workflows"

    @staticmethod
    def load(prompt, width, height, seed):
        path = WorkflowLoader.WORKFLOW_DIR / "z_image_text_to_image_api.json"

        with open(path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        # Working Z-Image-Turbo workflow
        workflow["63"]["inputs"]["clip_name1"] = "qwen_3_4b_fp4_mixed.safetensors"
        workflow["63"]["inputs"]["clip_name2"] = "qwen_3_4b_fp4_mixed.safetensors"

        workflow["57:28"]["inputs"]["unet_name"] = "z_image_turbo_nvfp4.safetensors"

        workflow["57:27"]["inputs"]["text"] = prompt

        workflow["57:13"]["inputs"]["width"] = width
        workflow["57:13"]["inputs"]["height"] = height
        workflow["57:13"]["inputs"]["batch_size"] = 1

        workflow["57:3"]["inputs"]["seed"] = seed

        return workflow
