from pathlib import Path
import wave

from config.paths import VOICE_REFERENCES
from core.media_references import AUDIO_EXTENSIONS, MEDIA_LIMITS


MIN_REFERENCE_DURATION_SECONDS = 2
MAX_REFERENCE_DURATION_SECONDS = 10


def _validate_duration(path):
    if path.suffix.lower() != ".wav":
        return
    try:
        with wave.open(str(path), "rb") as audio:
            frame_rate = audio.getframerate()
            frame_count = audio.getnframes()
    except (OSError, wave.Error) as error:
        raise ValueError("Reference WAV audio could not be read.") from error
    duration = frame_count / frame_rate if frame_rate > 0 else 0
    if not MIN_REFERENCE_DURATION_SECONDS <= duration <= MAX_REFERENCE_DURATION_SECONDS:
        raise ValueError(
            "Reference audio must be between 2 and 10 seconds."
        )


def validate_managed_reference(filename):
    if not isinstance(filename, str) or not filename:
        raise ValueError("Invalid reference audio filename.")
    if Path(filename).name != filename:
        raise ValueError("Invalid reference audio filename.")

    extension = Path(filename).suffix.lower()
    if extension not in AUDIO_EXTENSIONS:
        raise ValueError("Unsupported reference audio format.")

    candidate = VOICE_REFERENCES / filename
    if candidate.is_symlink():
        raise ValueError("Reference audio symlinks are not allowed.")

    managed_root = VOICE_REFERENCES.resolve()
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(managed_root)
    except ValueError as error:
        raise ValueError("Invalid reference audio filename.") from error

    if not resolved.is_file():
        raise ValueError("Reference audio file was not found.")

    try:
        size = resolved.stat().st_size
    except OSError as error:
        raise ValueError("Unable to inspect reference audio file.") from error
    if size > MEDIA_LIMITS[extension]:
        raise ValueError("Reference audio file is too large.")

    _validate_duration(resolved)
    return resolved
