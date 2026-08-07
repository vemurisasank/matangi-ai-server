from pydantic import BaseModel


class VoiceRequest(BaseModel):

    text: str

    voice: str = "female"

    language: str = "English"

    speed: float = 1.0