from pathlib import Path
import time
import uuid

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from core import media_references
from core.logger import Logger


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
        return written
    except FileExistsError:
        raise
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def _failure_response(message, status_code):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
        },
    )


def _cleanup_destination(destination, generated_filename):
    if destination is None:
        return
    try:
        destination.unlink(missing_ok=True)
    except OSError as error:
        Logger.error(
            "upload.cleanup_failed "
            f"filename={generated_filename!r} reason={str(error)!r}"
        )
        return
    Logger.info(
        "upload.cleanup_completed "
        f"filename={generated_filename!r}"
    )


@router.post("/upload")
async def upload_reference(
    request: Request,
    file: UploadFile = File(...)
):

    destination = None
    generated_filename = None
    started_at = time.monotonic()
    Logger.info("upload.request_accepted")
    try:

        media_references.COMFY_INPUT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = file.filename or ""
        extension = Path(filename).suffix.lower()
        Logger.info(
            "upload.metadata_received "
            f"original_filename={filename!r} extension={extension!r}"
        )

        if not filename or extension not in MEDIA_LIMITS:

            message = "Unsupported reference file format."
            Logger.warning(
                f"upload.failed reason={message!r}"
            )
            Logger.info(
                f"upload.response outcome=failure status_code=400"
            )
            return _failure_response(message, 400)

        generated_filename = (
            f"matangi_reference_"
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )
        Logger.info(
            "upload.destination_generated "
            f"original_filename={filename!r} "
            f"generated_filename={generated_filename!r}"
        )

        destination = (
            media_references.COMFY_INPUT_DIR / generated_filename
        )

        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                Logger.warning(
                    f"upload.invalid_content_length value={content_length!r}"
                )
            else:
                if declared_size > MEDIA_LIMITS[extension]:
                    message = "Uploaded file exceeds the permitted size."
                    Logger.warning(
                        "upload.failed "
                        f"reason={message!r} "
                        f"declared_size={declared_size}"
                    )
                    Logger.info(
                        "upload.response outcome=failure status_code=413"
                    )
                    return _failure_response(message, 413)

        Logger.info(
            "upload.copy_started "
            f"generated_filename={generated_filename!r}"
        )
        written = await _copy_upload(
            file,
            destination,
            MEDIA_LIMITS[extension],
        )
        duration = time.monotonic() - started_at
        Logger.info(
            "upload.copy_completed "
            f"generated_filename={generated_filename!r} "
            f"bytes={written} duration_seconds={duration:.3f}"
        )
        Logger.info("upload.response outcome=success status_code=200")

        return {
            "success": True,
            "message": _media_message(extension),
            "data": {
                "filename": generated_filename
            }
        }

    except ValueError as error:
        Logger.warning(
            "upload.failed "
            f"filename={generated_filename!r} reason={str(error)!r}"
        )
        _cleanup_destination(destination, generated_filename)
        Logger.info("upload.response outcome=failure status_code=413")
        return _failure_response(str(error), 413)

    except FileExistsError:
        message = "Unable to store the uploaded reference file."
        Logger.error(
            "upload.failed "
            f"filename={generated_filename!r} reason={message!r}"
        )
        Logger.info("upload.response outcome=failure status_code=500")
        return _failure_response(message, 500)

    except (OSError, RuntimeError):
        message = "Unable to store the uploaded reference file."
        Logger.error(
            "upload.failed "
            f"filename={generated_filename!r} reason={message!r}"
        )
        _cleanup_destination(destination, generated_filename)
        Logger.info("upload.response outcome=failure status_code=500")
        return _failure_response(message, 500)

    finally:
        await file.close()