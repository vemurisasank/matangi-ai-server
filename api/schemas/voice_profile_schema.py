from typing import Any

from pydantic import BaseModel, Field


class VoiceProfileCreateRequest(BaseModel):
    character_id: str = ""
    reference_audio_filename: str
    reference_transcript: str = ""
    language: str = "Telugu"
    model: str = "shankarpandala/chatterbox-telugu"
    generation_settings: dict[str, Any] = Field(default_factory=dict)


class VoiceProfileUpdateRequest(BaseModel):
    character_id: str | None = None
    reference_audio_filename: str | None = None
    reference_transcript: str | None = None
    language: str | None = None
    model: str | None = None
    generation_settings: dict[str, Any] | None = None
