from fastapi import APIRouter

from core.response_manager import ResponseManager

from config.constants import VERSION


router = APIRouter()


@router.get("/version")

def version():

    return ResponseManager.success(

        {

            "version": VERSION

        },

        "Version Retrieved"

    )