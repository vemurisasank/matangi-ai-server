from pydantic import BaseModel


class ImageRequest(BaseModel):

    prompt: str

    style: str = "Cinematic"

    aspect_ratio: str = "16:9"

    width: int = 1280

    height: int = 720

    seed: int = -1