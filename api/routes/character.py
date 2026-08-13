from fastapi import APIRouter

from api.schemas.character_schema import CharacterRequest

from engines.character_engine import CharacterEngine

from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/character")
def generate_character(request: CharacterRequest):

    try:

        result = CharacterEngine.generate(
            request
        )

        return ResponseManager.success(
            result,
            "Character Generated Successfully"
        )

    except Exception as e:

        return ResponseManager.failure(
            str(e)
        )
