from fastapi import APIRouter

from core.server_context import server

from core.response_manager import ResponseManager

router = APIRouter()


@router.get("/models")

def get_models():

    return ResponseManager.success(

        server.model_manager.get_all_models(),

        "Models Retrieved Successfully"

    )