from pydantic import BaseModel, Field


class ImageRequest(BaseModel):

    prompt: str

    style: str = "Cinematic"

    aspect_ratio: str = "16:9"

    width: int = Field(
        default=1280,
        gt=0
    )

    height: int = Field(
        default=720,
        gt=0
    )

    seed: int = -1

    reference_images: list[dict] = Field(
        default_factory=list,
        max_length=3
    )

    model: str | None = None

    steps: int = Field(
        default=20,
        gt=0
    )

    cfg: float = Field(
        default=4.0,
        ge=0.0
    )

    sampler: str = "euler"

    scheduler: str = "simple"

    model_config = {
        "extra": "ignore"
    }