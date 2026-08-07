from fastapi import APIRouter

from core.response_manager import ResponseManager

router = APIRouter()


@router.get("/health")

def health():

    return ResponseManager.success(

        {

            "status":"Healthy",

            "server":"MATANGI AI SERVER",

            "version":"1.0.0"

        },

        "Server Running"

    )