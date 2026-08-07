from fastapi import APIRouter

from core.server_context import server
from core.response_manager import ResponseManager

router = APIRouter()


@router.get("/providers")
def get_providers():

    try:

        return ResponseManager.success(

            {

                "providers": server.provider_manager.list()

            },

            "Providers Retrieved Successfully"

        )

    except Exception as e:

        return ResponseManager.failure(

            str(e)

        )