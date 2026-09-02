from pydantic import BaseModel, Field


class ImageRequest(BaseModel):

    prompt: str

    style: str = "Cinematic"

    aspect_ratio: str = "16:9"

    width: int = 1280

    height: int = 720

    seed: int = -1

    reference_images: list[dict] = Field(
        default_factory=list
    )