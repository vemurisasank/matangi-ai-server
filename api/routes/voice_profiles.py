from datetime import datetime, timezone
from pathlib import Path
import uuid

from fastapi import APIRouter, File, UploadFile

from api.schemas.voice_profile_schema import (
    VoiceProfileCreateRequest,
    VoiceProfileUpdateRequest,
)
from config.paths import VOICE_REFERENCES
from core.media_references import AUDIO_EXTENSIONS, MEDIA_LIMITS
from core.response_manager import ResponseManager
from core.server_context import server
from core.voice_reference_storage import validate_managed_reference
from models.voice_profile import VoiceProfile


router = APIRouter()
CHUNK_SIZE = 1024 * 1024


def _serialize(profile):
    return {
        "id": profile.id,
        "character_id": profile.character_id,
        "reference_audio_filename": profile.reference_audio_filename,
        "reference_transcript": profile.reference_transcript,
        "language": profile.language,
        "model": profile.model,
        "generation_settings": profile.generation_settings,
        "created_on": profile.created_on,
        "updated_on": profile.updated_on,
    }


def _validate_reference_filename(filename):
    validate_managed_reference(filename)
    return filename


@router.post("/voice-profiles")
def create_voice_profile(request: VoiceProfileCreateRequest):
    try:
        filename = _validate_reference_filename(
            request.reference_audio_filename
        )
        now = datetime.now(timezone.utc).isoformat()
        profile = VoiceProfile(
            id=f"voice_{uuid.uuid4().hex}",
            character_id=request.character_id,
            reference_audio_filename=filename,
            reference_transcript=request.reference_transcript,
            language=request.language,
            model=request.model,
            generation_settings=request.generation_settings,
            created_on=now,
            updated_on=now,
        )
        server.voice_profile_manager.create(profile)
        return ResponseManager.success(
            _serialize(profile),
            "Voice Profile Created Successfully",
        )
    except Exception as error:
        return ResponseManager.failure(str(error))


@router.get("/voice-profiles")
def list_voice_profiles():
    return ResponseManager.success(
        [_serialize(profile) for profile in server.voice_profile_manager.get_all()],
        "Voice Profiles Retrieved Successfully",
    )


@router.get("/voice-profiles/{profile_id}")
def get_voice_profile(profile_id: str):
    profile = server.voice_profile_manager.get(profile_id)
    if profile is None:
        return ResponseManager.failure("Voice profile was not found.")
    return ResponseManager.success(
        _serialize(profile),
        "Voice Profile Retrieved Successfully",
    )


@router.patch("/voice-profiles/{profile_id}")
def update_voice_profile(
    profile_id: str,
    request: VoiceProfileUpdateRequest,
):
    try:
        changes = request.model_dump(exclude_unset=True)
        if "reference_audio_filename" in changes:
            changes["reference_audio_filename"] = _validate_reference_filename(
                changes["reference_audio_filename"]
            )
        profile = server.voice_profile_manager.update(
            profile_id,
            **changes,
            updated_on=datetime.now(timezone.utc).isoformat(),
        )
        if profile is None:
            return ResponseManager.failure("Voice profile was not found.")
        return ResponseManager.success(
            _serialize(profile),
            "Voice Profile Updated Successfully",
        )
    except Exception as error:
        return ResponseManager.failure(str(error))


@router.post("/voice-profiles/reference")
async def upload_voice_reference(file: UploadFile = File(...)):
    destination = None
    try:
        filename = file.filename or ""
        extension = Path(filename).suffix.lower()
        if extension not in AUDIO_EXTENSIONS:
            return ResponseManager.failure(
                "Unsupported reference audio format."
            )
        VOICE_REFERENCES.mkdir(parents=True, exist_ok=True)
        generated_filename = f"voice_reference_{uuid.uuid4().hex}{extension}"
        destination = VOICE_REFERENCES / generated_filename
        written = 0
        with destination.open("xb") as output:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > MEDIA_LIMITS[extension]:
                    raise ValueError("Reference audio file is too large.")
                output.write(chunk)
        validate_managed_reference(generated_filename)
        return ResponseManager.success(
            {"filename": generated_filename},
            "Voice Reference Uploaded Successfully",
        )
    except FileExistsError:
        return ResponseManager.failure(
            "Unable to store the uploaded reference audio."
        )
    except Exception as error:
        if destination is not None:
            destination.unlink(missing_ok=True)
        return ResponseManager.failure(str(error))
    finally:
        await file.close()
