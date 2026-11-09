import wave

import pytest

from core import voice_reference_storage


def _write_wav(path, seconds):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(b"\x00\x00" * int(24000 * seconds))


@pytest.mark.parametrize("seconds", [2, 10])
def test_managed_reference_duration_boundaries_are_accepted(
    tmp_path, monkeypatch, seconds
):
    reference = tmp_path / "reference.wav"
    _write_wav(reference, seconds)
    monkeypatch.setattr(
        voice_reference_storage,
        "VOICE_REFERENCES",
        tmp_path,
    )

    assert voice_reference_storage.validate_managed_reference(
        "reference.wav"
    ) == reference


@pytest.mark.parametrize("seconds", [1.99, 10.01])
def test_managed_reference_duration_outside_bounds_is_rejected(
    tmp_path, monkeypatch, seconds
):
    reference = tmp_path / "reference.wav"
    _write_wav(reference, seconds)
    monkeypatch.setattr(
        voice_reference_storage,
        "VOICE_REFERENCES",
        tmp_path,
    )

    with pytest.raises(ValueError, match="between 2 and 10 seconds"):
        voice_reference_storage.validate_managed_reference(
            "reference.wav"
        )
