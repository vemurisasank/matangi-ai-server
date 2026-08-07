from fastapi import Request
from fastapi.responses import JSONResponse

from core.response_manager import ResponseManager
from core.logger import Logger


class ExceptionManager:

    @staticmethod
    async def handle_exception(
        request: Request,
        exc: Exception
    ):

        Logger.error(str(exc))

        return JSONResponse(

            status_code=500,

            content=ResponseManager.failure(

                f"Internal Server Error : {str(exc)}"

            )

        )