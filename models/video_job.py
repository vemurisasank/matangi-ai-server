from dataclasses import dataclass, field


@dataclass
class VideoJob:
    job_id: str
    type: str = "video"
    provider: str = "comfyui"
    model: str = "minimax-h3"
    status: str = "queued"
    progress: int | None = None
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    prompt: str = ""
    duration: int = 5
    fps: int = 24
    width: int = 512
    height: int = 512
    reference_image: str | None = None
    reference_images: list[str] = field(default_factory=list)
    reference_metadata: list[dict[str, str]] | None = None
    seed: int | None = None
    scene_id: str | None = None
    project: str | None = None
    comfy_prompt_id: str | None = None
    output_filename: str | None = None
    output_subfolder: str = ""
    output_type: str = "output"
    output_path: str | None = None
    error: str | None = None
