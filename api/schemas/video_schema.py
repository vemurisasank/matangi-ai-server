from pydantic import BaseModel


class VideoRequest(BaseModel):

    prompt: str

    duration: int = 5

    fps: int = 24

    width: int = 1280

    height: int = 720