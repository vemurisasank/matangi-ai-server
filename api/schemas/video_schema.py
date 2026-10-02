from pydantic import BaseModel, Field


class ReferenceMetadata(BaseModel):
    type: str
    name: str


class VideoRequest(BaseModel):

    prompt: str

    duration: int = 5

    fps: int = 24

    width: int = 1280

    height: int = 720

    reference_image: str | None = None

    scene_id: str | None = None

    project: str | None = None

    model: str | None = None

    seed: int | None = None


class AsyncVideoRequest(BaseModel):
    prompt: str
    duration: int = 5
    fps: int = 24
    width: int = 512
    height: int = 512
    reference_image: str | None = None
    reference_images: list[str] = Field(default_factory=list, max_length=9)
    ref_images: dict[str, str] | None = None
    reference_metadata: list[ReferenceMetadata] | None = Field(
        default=None,
        max_length=9
    )
    scene_id: str | None = None
    project: str | None = None
    model: str | None = None
    seed: int | None = None
