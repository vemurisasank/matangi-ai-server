from typing import Any

from pydantic import BaseModel, Field


class VoiceRequest(BaseModel):

    text: str

    voice: str = "female"

    language: str = "English"

    speed: float = 1.0

    profile_id: str | None = None

    reference_audio_filename: str | None = None

    reference_transcript: str = ""

    generation_settings: dict[str, Any] = Field(
        default_factory=dict
    )