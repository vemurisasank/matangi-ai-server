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
            / "ltx_2_3_i2v_api.json"
        )

        with open(path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        # Keep the proven LTX-2.3 model configuration.
        workflow["320:316"]["inputs"]["ckpt_name"] = (
            "ltx-2.3-22b-distilled-fp8.safetensors"
        )

        workflow["320:317"]["inputs"]["text_encoder"] = (
            "gemma_3_12B_it_fp4_mixed.safetensors"
        )

        # Reference image.
        # The actual LoadImage node is connected to 320:289.
        for node_id, node in workflow.items():
            if node.get("class_type") == "LoadImage":
                node["inputs"]["image"] = reference_image

        # Prompt used by the LTX prompt generator.
        if "320:319" in workflow:
            workflow["320:319"]["inputs"]["value"] = prompt

        # Reference-image influence.
        if "320:296" in workflow:
            workflow["320:296"]["inputs"]["strength"] = 0.7

        # Video dimensions.
        if "320:299" in workflow:
            workflow["320:299"]["inputs"]["value"] = width

        if "320:300" in workflow:
            workflow["320:300"]["inputs"]["value"] = fps

        # Keep the successful workflow's default quality parameters.
        if "320:301" in workflow:
            workflow["320:301"]["inputs"]["value"] = 5

        # Seed is present in the prompt-generation node.
        if "320:325" in workflow:
            workflow["320:325"]["inputs"]["sampling_mode.seed"] = seed

        # Video output FPS.
        if "320:310" in workflow:
            workflow["320:310"]["inputs"]["fps"] = [
                "320:298",
                0
            ]

        return workflow
