from pathlib import Path
import uuid

from fastapi import APIRouter, File, UploadFile

from core import media_references


router = APIRouter()


COMFY_INPUT_DIR = media_references.COMFY_INPUT_DIR
CHUNK_SIZE = 1024 * 1024
MEDIA_LIMITS = media_references.MEDIA_LIMITS
IMAGE_EXTENSIONS = media_references.IMAGE_EXTENSIONS


def _media_message(extension):
    if extension in IMAGE_EXTENSIONS:
        return "Reference image uploaded successfully."
    return "Reference file uploaded successfully."


async def _copy_upload(file, destination, limit):
    written = 0
    try:
        with destination.open("xb") as buffer:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > limit:
                    raise ValueError("Uploaded file exceeds the permitted size.")
                buffer.write(chunk)
    except FileExistsError:
        raise
    except Exception:
        destination.unlink(missing_ok=True)
        raise


@router.post("/upload")
async def upload_reference(
    file: UploadFile = File(...)
):

    destination = None
    try:

        media_references.COMFY_INPUT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = file.filename or ""
        extension = Path(filename).suffix.lower()

        if not filename or extension not in MEDIA_LIMITS:

            return {
                "success": False,
                "message": "Unsupported reference file format.",
                "data": None
            }

        generated_filename = (
            f"matangi_reference_"
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )

        destination = (
            media_references.COMFY_INPUT_DIR / generated_filename
        )

        await _copy_upload(file, destination, MEDIA_LIMITS[extension])

        return {
            "success": True,
            "message": _media_message(extension),
            "data": {
                "filename": generated_filename
            }
        }

    except ValueError as error:
        if destination is not None:
            destination.unlink(missing_ok=True)
        return {
            "success": False,
            "message": str(error),
            "data": None
        }

    except FileExistsError:
        return {
            "success": False,
            "message": "Unable to store the uploaded reference file.",
            "data": None
        }

    except (OSError, RuntimeError):
        if destination is not None:
            destination.unlink(missing_ok=True)
        return {
            "success": False,
            "message": "Unable to store the uploaded reference file.",
            "data": None
        }

    finally:
        await file.close()