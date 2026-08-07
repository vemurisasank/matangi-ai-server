from fastapi import APIRouter

from api.schemas.render_schema import RenderRequest

from engines.render_engine import RenderEngine

from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/render")

def render_movie(request: RenderRequest):

    try:
        result = RenderEngine.render(request)

        return ResponseManager.success(

            result,

            "Render Started Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )