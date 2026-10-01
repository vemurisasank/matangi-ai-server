import json
from pathlib import Path


class MiniMaxH3VideoWorkflowLoader:

    WORKFLOW_DIR = Path(__file__).resolve().parents[2] / "workflows"

    @staticmethod
    def _frame_count(duration):
        frames = max(5, round(duration * 24))
        return frames + (5 - (frames % 17)) % 17

    @staticmethod
    def load(
        prompt,
        reference_image,
        width=512,
        height=512,
        duration=5,
        fps=24,
        seed=0
    ):
        if fps != 24:
            raise ValueError("MiniMax H3 requires fps=24.")

        path = (
            MiniMaxH3VideoWorkflowLoader.WORKFLOW_DIR
            / "minimax_h3_i2v_api.json"
        )

        with path.open("r", encoding="utf-8") as f:
            workflow = json.load(f)

        filename = Path(reference_image).name
        workflow["1"]["inputs"]["image"] = filename
        workflow["6"]["inputs"]["prompt"] = prompt
        workflow["6"]["inputs"]["width"] = width
        workflow["6"]["inputs"]["height"] = height
        workflow["6"]["inputs"]["length"] = (
            MiniMaxH3VideoWorkflowLoader._frame_count(duration)
        )
        workflow["7"]["inputs"]["noise_seed"] = seed

        return workflow
