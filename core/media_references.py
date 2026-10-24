from pathlib import Path


COMFY_INPUT_DIR = Path("/workspace/ComfyUI/input")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".oga"
}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

MEDIA_LIMITS = {
    **{extension: 20 * 1024 * 1024 for extension in IMAGE_EXTENSIONS},
    **{extension: 50 * 1024 * 1024 for extension in AUDIO_EXTENSIONS},
    **{extension: 200 * 1024 * 1024 for extension in VIDEO_EXTENSIONS},
}

MEDIA_EXTENSIONS = {
    "image": IMAGE_EXTENSIONS,
    "audio": AUDIO_EXTENSIONS,
    "video": VIDEO_EXTENSIONS,
}


class MediaReferenceValidationError(ValueError):
    """Raised when a submitted media reference is not safely staged."""


def validate_reference(reference, media_type):
    if media_type not in MEDIA_EXTENSIONS:
        raise ValueError("Unsupported media reference type.")
    if not isinstance(reference, str) or not reference.strip():
        raise MediaReferenceValidationError(
            f"Invalid {media_type} reference filename."
        )

    if (
        Path(reference).is_absolute()
        or "/" in reference
        or "\\" in reference
        or Path(reference).name != reference
    ):
        raise MediaReferenceValidationError(
            f"Invalid {media_type} reference filename."
        )

    extension = Path(reference).suffix.lower()
    if extension not in MEDIA_EXTENSIONS[media_type]:
        raise MediaReferenceValidationError(
            f"Unsupported {media_type} reference format."
        )

    input_dir = COMFY_INPUT_DIR.resolve()
    candidate = (input_dir / reference).resolve(strict=False)
    try:
        candidate.relative_to(input_dir)
    except ValueError as error:
        raise MediaReferenceValidationError(
            f"Invalid {media_type} reference filename."
        ) from error

    if candidate.is_symlink() or not candidate.is_file():
        raise MediaReferenceValidationError(
            f"{media_type.capitalize()} reference file was not found."
        )

    try:
        size = candidate.stat().st_size
    except OSError as error:
        raise MediaReferenceValidationError(
            f"Unable to inspect {media_type} reference file."
        ) from error
    if size > MEDIA_LIMITS[extension]:
        raise MediaReferenceValidationError(
            f"{media_type.capitalize()} reference file is too large."
        )

    return reference
