from fastapi import APIRouter

from api.schemas.three_d_schema import ThreeDRequest
from engines.three_d_engine import ThreeDEngine
from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/3d")
def generate_3d(request: ThreeDRequest):

    try:

        result = ThreeDEngine.generate(
            request
        )

        if result.get("success"):

            return ResponseManager.success(
                result,
                "3D Asset Generated Successfully"
            )

        return ResponseManager.failure(
            result.get(
                "error",
                "3D asset generation failed."
            )
        )

    except Exception as e:

        return ResponseManager.failure(
            str(e)
        )
