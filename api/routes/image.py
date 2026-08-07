from fastapi import APIRouter

from api.schemas.image_schema import ImageRequest

from engines.image_engine import ImageEngine

from core.response_manager import ResponseManager

router = APIRouter()


@router.post("/image")

def generate_image(request: ImageRequest):
    try:
        result = ImageEngine.generate(request)

        return ResponseManager.success(

            result,

            "Image Generated Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )