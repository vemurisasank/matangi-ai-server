from pydantic import BaseModel


class MusicRequest(BaseModel):

    prompt: str

    duration: int = 30

    style: str = "Cinematic"