from fastapi import APIRouter

from api.schemas.script_schema import ScriptRequest

from engines.script_engine import ScriptEngine

from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/script")
def generate_script(
    request: ScriptRequest
):

    try:

        result = ScriptEngine.generate(

            title=request.title,

            description=request.description,

            style=request.style,

            language=request.language,

            task=request.task

        )

        if not result.get("success", False):

            return ResponseManager.failure(

                result.get(
                    "message",
                    "Script generation failed."
                )

            )

        return ResponseManager.success(

            result.get(
                "data",
                ""
            ),

            "Script Generated Successfully"

        )

    except Exception as e:

        return ResponseManager.failure(
            str(e)
        )