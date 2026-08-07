from fastapi import APIRouter
from pydantic import BaseModel
from engines.script_engine import ScriptEngine
from core.server_context import server
from core.response_manager import ResponseManager

router = APIRouter()


class ScriptRequest(BaseModel):

    prompt: str


@router.post("/script")
def generate_script(request: ScriptRequest):

    try:

        result = ScriptEngine.generate(

        request.prompt

        )

        return ResponseManager.success(

            result,

            "Script Generated Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )