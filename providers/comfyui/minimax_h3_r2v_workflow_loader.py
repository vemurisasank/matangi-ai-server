import json
from pathlib import Path


class MiniMaxH3R2VWorkflowLoader:
    WORKFLOW_DIR = Path(__file__).resolve().parents[2] / "workflows"
    MAX_REFERENCES = 9
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 704
    COMPATIBLE_DIMENSIONS = {(512, 512), (1024, 704)}
    REQUIRED_FPS = 24
    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

    @staticmethod
    def _frame_count(duration):
        frames = max(5, round(duration * 24))
        return frames + (5 - (frames % 17)) % 17

    @classmethod
    def load(
        cls,
        prompt,
        references,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        duration=5,
        fps=REQUIRED_FPS,
        seed=0
    ):
        if fps != cls.REQUIRED_FPS:
            raise ValueError("MiniMax H3 requires fps=24.")
        if (width, height) not in cls.COMPATIBLE_DIMENSIONS:
            raise ValueError(
                "MiniMax H3 R2V requires 512x512 or 1024x704."
            )
        if not isinstance(references, (list, tuple)):
            raise ValueError("R2V references must be provided as an ordered list.")
        if len(references) > cls.MAX_REFERENCES:
            raise ValueError("MiniMax H3 R2V supports at most 9 references.")

        path = cls.WORKFLOW_DIR / "minimax_h3_r2v_api.json"
        with path.open("r", encoding="utf-8") as file:
            workflow = json.load(file)

        inputs = workflow["6"]["inputs"]
        inputs["prompt"] = prompt
        inputs["width"] = width
        inputs["height"] = height
        inputs["length"] = cls._frame_count(duration)
        inputs["ref_image_size"] = "match"
        workflow["7"]["inputs"]["noise_seed"] = seed

        for index in range(cls.MAX_REFERENCES):
            inputs.pop(f"ref_images.ref_image_{index}", None)
            workflow.pop(str(21 + index), None)

        for index, reference in enumerate(references):
            if reference is None:
                continue
            filename = Path(reference).name
            if (
                not filename
                or Path(filename).suffix.lower() not in cls.IMAGE_SUFFIXES
            ):
                raise ValueError("Each R2V reference must be a valid image path.")
            inputs[f"ref_images.ref_image_{index}"] = [str(21 + index), 0]
            workflow[str(21 + index)] = {
                "class_type": "LoadImage",
                "inputs": {"image": filename}
            }

        return workflow
