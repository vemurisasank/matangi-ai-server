from fastapi import APIRouter

from api.schemas.prompt_schema import PromptRequest

from core.prompt_builder import PromptBuilder

from core.server_context import server

from core.response_manager import ResponseManager
from engines.prompt_engine import PromptEngine

router = APIRouter()


@router.post("/prompt")

def generate_prompt(

    request: PromptRequest

):
    try:

        result = PromptEngine.generate(

            request

        )

        return ResponseManager.success(

            result,

            "Scene Prompts Generated Successfully"

        )
    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )