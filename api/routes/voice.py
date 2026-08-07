from fastapi import APIRouter

from api.schemas.voice_schema import VoiceRequest

from engines.voice_engine import VoiceEngine

from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/voice")

def generate_voice(request: VoiceRequest):

    try:

        result = VoiceEngine.generate(request)

        return ResponseManager.success(

            result,

            "Voice Generated Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )