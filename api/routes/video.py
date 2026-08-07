from fastapi import APIRouter

from api.schemas.video_schema import VideoRequest

from engines.video_engine import VideoEngine

from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/video")

def generate_video(request: VideoRequest):

    try:

        result = VideoEngine.generate(request)

        return ResponseManager.success(

            result,

            "Video Generated Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )