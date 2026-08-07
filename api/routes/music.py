from fastapi import APIRouter

from api.schemas.music_schema import MusicRequest

from engines.music_engine import MusicEngine

from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/music")

def generate_music(request: MusicRequest):

    try:
        result = MusicEngine.generate(request)

        return ResponseManager.success(

            result,

            "Music Generated Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )