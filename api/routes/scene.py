from fastapi import APIRouter

from api.schemas.scene_schema import SceneRequest

from engines.scene_engine import SceneEngine

from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/scene")
def generate_scene(request: SceneRequest):

    try:

        result = SceneEngine.generate(
            request
        )

        return ResponseManager.success(
            result,
            "Scenes Generated Successfully"
        )

    except Exception as e:

        return ResponseManager.failure(
            str(e)
        )
