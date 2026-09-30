import json
from pathlib import Path


class LTXVideoWorkflowLoader:

    WORKFLOW_DIR = Path(__file__).resolve().parents[2] / "workflows"

    @staticmethod
    def load(
        prompt,
        reference_image,
        width=1024,
        height=576,
        duration=5,
        fps=25,
        seed=0
    ):
        path = (
            LTXVideoWorkflowLoader.WORKFLOW_DIR
            / "ltxv_0_9_8_2b_i2v_api.json"
        )

        with open(path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        for node_id, node in workflow.items():
            if node.get("class_type") == "LoadImage":
                node["inputs"]["image"] = reference_image

        workflow["4"]["inputs"]["text"] = prompt
        workflow["16"]["inputs"]["value"] = width
        workflow["17"]["inputs"]["value"] = height
        workflow["18"]["inputs"]["value"] = fps
        workflow["19"]["inputs"]["value"] = duration * fps + 1
        workflow["9"]["inputs"]["noise_seed"] = seed

        return workflow
