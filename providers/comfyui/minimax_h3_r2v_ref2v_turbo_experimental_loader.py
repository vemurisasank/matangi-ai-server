import json
from pathlib import Path


class MiniMaxH3R2VRef2VTurboExperimentalLoader:
    WORKFLOW_DIR = Path(__file__).resolve().parents[2] / "workflows"
    WORKFLOW_NAME = "minimax_h3_r2v_ref2v_turbo_4step_experimental.json"
    MAX_REFERENCES = 9
    WIDTH = 1280
    HEIGHT = 704
    REQUIRED_FPS = 24
    LENGTH = 124
    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

    @classmethod
    def load(
        cls,
        prompt,
        references,
        width=WIDTH,
        height=HEIGHT,
        duration=5,
        fps=REQUIRED_FPS,
        seed=0
    ):
        if fps != cls.REQUIRED_FPS:
            raise ValueError("MiniMax H3 requires fps=24.")
        if (width, height) != (cls.WIDTH, cls.HEIGHT):
            raise ValueError("Experimental Ref2V Turbo requires 1280x704.")
        if duration != 5:
            raise ValueError("Experimental Ref2V Turbo requires duration=5.")
        if not isinstance(references, (list, tuple)):
            raise ValueError("R2V references must be provided as an ordered list.")
        if not 1 <= len(references) <= cls.MAX_REFERENCES:
            raise ValueError("Experimental Ref2V Turbo requires 1 to 9 references.")

        path = cls.WORKFLOW_DIR / cls.WORKFLOW_NAME
        with path.open("r", encoding="utf-8") as file:
            workflow = json.load(file)

        inputs = workflow["6"]["inputs"]
        inputs["prompt"] = prompt
        inputs["width"] = cls.WIDTH
        inputs["height"] = cls.HEIGHT
        inputs["length"] = cls.LENGTH
        inputs["ref_image_size"] = "match"
        workflow["7"]["inputs"]["noise_seed"] = seed

        for index in range(cls.MAX_REFERENCES):
            inputs.pop(f"ref_images.ref_image_{index}", None)
            workflow.pop(str(21 + index), None)

        for index, reference in enumerate(references):
            if reference is None:
                raise ValueError("R2V references cannot contain None.")
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
