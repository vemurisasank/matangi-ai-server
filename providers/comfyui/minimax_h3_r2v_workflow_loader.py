import json
from pathlib import Path


class MiniMaxH3R2VWorkflowLoader:
    WORKFLOW_DIR = Path(__file__).resolve().parents[2] / "workflows"
    MAX_REFERENCES = 9
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 704
    COMPATIBLE_DIMENSIONS = {
        (512, 512),
        (640, 352),
        (1024, 704),
        (1280, 704)
    }
    REQUIRED_FPS = 24
    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".oga"}
    VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
    MAX_AUDIO_REFERENCES = 3
    MAX_VIDEO_REFERENCES = 3

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
        seed=0,
        audio_references=None,
        video_references=None
    ):
        if fps != cls.REQUIRED_FPS:
            raise ValueError("MiniMax H3 requires fps=24.")
        if (width, height) not in cls.COMPATIBLE_DIMENSIONS:
            raise ValueError(
                "MiniMax H3 R2V requires 512x512, 640x352, "
                "1024x704, or 1280x704."
            )
        if not isinstance(references, (list, tuple)):
            raise ValueError("R2V references must be provided as an ordered list.")
        if len(references) > cls.MAX_REFERENCES:
            raise ValueError("MiniMax H3 R2V supports at most 9 references.")
        if audio_references is None:
            audio_references = []
        if video_references is None:
            video_references = []
        if not isinstance(audio_references, (list, tuple)):
            raise ValueError("R2V audio references must be provided as an ordered list.")
        if not isinstance(video_references, (list, tuple)):
            raise ValueError("R2V video references must be provided as an ordered list.")
        if len(audio_references) > cls.MAX_AUDIO_REFERENCES:
            raise ValueError("MiniMax H3 R2V supports at most 3 audio references.")
        if len(video_references) > cls.MAX_VIDEO_REFERENCES:
            raise ValueError("MiniMax H3 R2V supports at most 3 video references.")

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
            filename = cls._staged_filename(reference, cls.IMAGE_SUFFIXES)
            if filename is None:
                raise ValueError("Each R2V reference must be a valid image path.")
            inputs[f"ref_images.ref_image_{index}"] = [str(21 + index), 0]
            workflow[str(21 + index)] = {
                "class_type": "LoadImage",
                "inputs": {"image": filename}
            }

        next_node_id = cls._next_node_id(workflow)
        for index, reference in enumerate(audio_references):
            filename = cls._staged_filename(reference, cls.AUDIO_SUFFIXES)
            if filename is None:
                raise ValueError("Each R2V audio reference must be a staged audio filename.")
            node_id = next_node_id
            next_node_id += 1
            workflow[str(node_id)] = {
                "class_type": "LoadAudio",
                "inputs": {"audio": filename}
            }
            inputs[f"ref_audios.ref_audio_{index}"] = [str(node_id), 0]

        for index, reference in enumerate(video_references):
            filename = cls._staged_filename(reference, cls.VIDEO_SUFFIXES)
            if filename is None:
                raise ValueError("Each R2V video reference must be a staged video filename.")
            load_node_id = next_node_id
            components_node_id = next_node_id + 1
            next_node_id += 2
            workflow[str(load_node_id)] = {
                "class_type": "LoadVideo",
                "inputs": {"file": filename}
            }
            workflow[str(components_node_id)] = {
                "class_type": "GetVideoComponents",
                "inputs": {"video": [str(load_node_id), 0]}
            }
            inputs[f"ref_videos.ref_video_{index}"] = [str(components_node_id), 0]
            inputs[f"ref_video_audios.ref_video_audio_{index}"] = [
                str(components_node_id),
                1
            ]

        return workflow

    @staticmethod
    def _next_node_id(workflow):
        numeric_ids = [
            int(node_id)
            for node_id in workflow
            if str(node_id).isdigit()
        ]
        return max(numeric_ids, default=0) + 1

    @staticmethod
    def _staged_filename(reference, suffixes):
        if not isinstance(reference, str) or not reference:
            return None
        path = Path(reference)
        if (
            path.is_absolute()
            or path.name != reference
            or "/" in reference
            or "\\" in reference
        ):
            return None
        if path.suffix.lower() not in suffixes:
            return None
        return reference
