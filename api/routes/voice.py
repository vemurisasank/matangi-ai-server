from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.schemas.voice_schema import VoiceRequest

from core.server_context import server
from engines.voice_engine import VoiceEngine

from core.response_manager import ResponseManager


router = APIRouter()


def _error_status(message):
    if "not found" in message.lower():
        return 404
    if "required" in message.lower() or "invalid" in message.lower():
        return 400
    if "dependencies" in message.lower() or "device" in message.lower():
        return 503
    return 500


def _failure(message, data=None, status_code=None):
    return JSONResponse(
        status_code=status_code or _error_status(message),
        content=ResponseManager.failure(message, data),
    )


@router.post("/voice")
def generate_voice(request: VoiceRequest):
    try:
        result = VoiceEngine.generate(request)
        if isinstance(result, dict) and result.get("success") is False:
            message = (
                result.get("message")
                or result.get("error")
                or "Voice generation failed."
            )
            return _failure(
                message,
            )
        return ResponseManager.success(
            result,
            "Voice Generated Successfully"
        )
    except ValueError as error:
        return _failure(str(error), status_code=400)
    except Exception:
        return _failure("Voice generation failed.")


@router.get("/voice/readiness")
def voice_readiness():
    try:
        provider = server.provider_manager.get("local-tts")
    except ValueError:
        return JSONResponse(
            status_code=503,
            content=ResponseManager.failure(
                "The local Telugu TTS provider is not registered."
            ),
        )

    readiness = provider.readiness()
    return ResponseManager.success(
        readiness,
        "Voice readiness retrieved.",
    )