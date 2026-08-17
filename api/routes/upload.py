from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import shutil
import uuid


router = APIRouter()


COMFY_INPUT_DIR = Path(
    "/workspace/ComfyUI/input"
)


@router.post("/upload")
async def upload_reference(
    file: UploadFile = File(...)
):

    try:

        COMFY_INPUT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        extension = Path(
            file.filename
        ).suffix.lower()

        if extension not in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        ]:

            return {
                "success": False,
                "message": "Unsupported image format.",
                "data": None
            }

        filename = (
            f"matangi_reference_"
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )

        destination = (
            COMFY_INPUT_DIR / filename
        )

        with destination.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        return {
            "success": True,
            "message": "Reference image uploaded successfully.",
            "data": {
                "filename": filename
            }
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e),
            "data": None
        }
