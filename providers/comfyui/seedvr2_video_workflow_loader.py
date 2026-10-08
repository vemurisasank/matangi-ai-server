import json
from pathlib import Path


class SeedVR2VideoWorkflowLoader:
    WORKFLOW_DIR = Path(__file__).resolve().parents[2] / "workflows"
    COMFY_INPUT_DIR = Path("/workspace/ComfyUI/input")
    WORKFLOW_NAME = "seedvr2_video_640x352_to_1280x720.json"

    @classmethod
    def load(cls, input_video_filename):
        filename = Path(input_video_filename).name
        if filename != input_video_filename:
            raise ValueError("SeedVR2 input must be a ComfyUI input filename.")
        if Path(filename).suffix.lower() != ".mp4":
            raise ValueError("SeedVR2 input must be an MP4 file.")

        input_path = cls.COMFY_INPUT_DIR / filename
        if not input_path.is_file():
            raise FileNotFoundError(
                f"SeedVR2 input video was not found: {input_path}"
            )

        path = cls.WORKFLOW_DIR / cls.WORKFLOW_NAME
        with path.open("r", encoding="utf-8") as file:
            workflow = json.load(file)

        workflow["1"]["inputs"]["file"] = filename
        return workflow
