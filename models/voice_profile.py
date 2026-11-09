from dataclasses import dataclass, field
from typing import Any


@dataclass
class VoiceProfile:
    id: str
    character_id: str
    reference_audio_filename: str
    reference_transcript: str = ""
    language: str = "Telugu"
    model: str = "shankarpandala/chatterbox-telugu"
    generation_settings: dict[str, Any] = field(default_factory=dict)
    created_on: str = ""
    updated_on: str = ""
