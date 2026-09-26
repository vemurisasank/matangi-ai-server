import json
import random
from pathlib import Path


class QwenImageT2IWorkflowLoader:

    WORKFLOW_PATH = (
        Path(__file__).resolve().parents[2]
        / "workflows"
        / "qwen_image_2512_text_to_image_api.json"
    )

    DEFAULT_NEGATIVE_PROMPT = (
        "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，"
        "人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲"
    )

    @classmethod
    def build(
        cls,
        prompt,
        negative_prompt="",
        width=1328,
        height=1328,
        seed=-1,
        steps=50,
        cfg=4.0,
        sampler="euler",
        scheduler="simple",
        reference_images=None
    ):
        references = reference_images or []
        if references:
            raise ValueError(
                "Qwen-Image-2512 text-to-image does not accept reference images."
            )

        if width <= 0 or height <= 0:
            raise ValueError("Qwen image width and height must be positive.")

        if steps <= 0:
            raise ValueError("Qwen image steps must be greater than zero.")

        if cfg < 0:
            raise ValueError("Qwen image cfg must be non-negative.")

        with cls.WORKFLOW_PATH.open("r", encoding="utf-8") as file:
            workflow = json.load(file)

        if seed < 0:
            seed = random.randint(0, 2**32 - 1)

        workflow["249"]["inputs"]["text"] = prompt
        workflow["250"]["inputs"]["text"] = (
            negative_prompt or cls.DEFAULT_NEGATIVE_PROMPT
        )
        workflow["252"]["inputs"].update({
            "width": width,
            "height": height
        })
        workflow["253"]["inputs"].update({
            "seed": seed,
            "sampler_name": sampler,
            "scheduler": scheduler
        })
        workflow["253"]["inputs"].update({
            "steps": steps,
            "cfg": cfg
        })
        workflow["save"]["inputs"]["filename_prefix"] = "qwen2512/image"

        return workflow
