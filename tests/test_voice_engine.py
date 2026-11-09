from types import SimpleNamespace

import pytest

from engines.voice_engine import VoiceEngine


def test_telugu_engine_forwards_optional_voice_fields(monkeypatch):
    calls = {}

    class FakeProvider:
        @staticmethod
        def validate_generation_settings(value):
            return value

        def generate_voice(self, **kwargs):
            calls.update(kwargs)
            return {"success": True}

    class FakeProviderManager:
        def get(self, name):
            assert name == "local-tts"
            return FakeProvider()

    monkeypatch.setattr(
        "engines.voice_engine.server.provider_manager",
        FakeProviderManager(),
    )

    request = SimpleNamespace(
        profile_id=None,
        reference_audio_filename=None,
        text="నమస్కారం",
        voice="female",
        language="Telugu",
        speed=1.0,
        generation_settings={},
    )

    result = VoiceEngine.generate(request)

    assert result["success"] is True
    assert calls["profile_id"] is None
    assert calls["reference_audio_filename"] is None
    assert calls["text"] == request.text
    assert calls["language"] == request.language


def _profile():
    return SimpleNamespace(
        id="voice-1",
        reference_audio_filename="reference.wav",
        reference_transcript="",
        language="Telugu",
        model="shankarpandala/chatterbox-telugu",
        generation_settings={"temperature": 0.7, "top_p": 0.9},
    )


def test_profile_settings_are_used_by_default(monkeypatch):
    calls = {}

    class FakeProvider:
        @staticmethod
        def validate_generation_settings(value):
            return value

        def generate_voice(self, **kwargs):
            calls.update(kwargs)
            return {"success": True}

    class FakeProviderManager:
        def get(self, name):
            return FakeProvider()

    class FakeProfiles:
        def get(self, profile_id):
            return _profile()

    monkeypatch.setattr(
        "engines.voice_engine.server.provider_manager",
        FakeProviderManager(),
    )
    monkeypatch.setattr(
        "engines.voice_engine.server.voice_profile_manager",
        FakeProfiles(),
    )
    monkeypatch.setattr(
        "engines.voice_engine.validate_managed_reference",
        lambda filename: None,
    )

    request = SimpleNamespace(
        profile_id="voice-1",
        reference_audio_filename=None,
        text="నమస్కారం",
        generation_settings={},
    )

    VoiceEngine.generate(request)

    assert calls["generation_settings"] == {
        "temperature": 0.7,
        "top_p": 0.9,
    }


def test_profile_settings_accept_valid_request_overrides(monkeypatch):
    calls = {}

    class FakeProvider:
        @staticmethod
        def validate_generation_settings(value):
            return value

        def generate_voice(self, **kwargs):
            calls.update(kwargs)
            return {"success": True}

    class FakeProviderManager:
        def get(self, name):
            return FakeProvider()

    class FakeProfiles:
        def get(self, profile_id):
            return _profile()

    monkeypatch.setattr(
        "engines.voice_engine.server.provider_manager",
        FakeProviderManager(),
    )
    monkeypatch.setattr(
        "engines.voice_engine.server.voice_profile_manager",
        FakeProfiles(),
    )
    monkeypatch.setattr(
        "engines.voice_engine.validate_managed_reference",
        lambda filename: None,
    )

    request = SimpleNamespace(
        profile_id="voice-1",
        reference_audio_filename=None,
        text="నమస్కారం",
        generation_settings={"temperature": 0.9},
    )

    VoiceEngine.generate(request)

    assert calls["generation_settings"] == {
        "temperature": 0.9,
        "top_p": 0.9,
    }


def test_invalid_profile_settings_are_rejected_before_generation(monkeypatch):
    class FakeProvider:
        @staticmethod
        def validate_generation_settings(value):
            raise ValueError("Unsupported Chatterbox generation settings.")

        def generate_voice(self, **kwargs):
            raise AssertionError("generation should not be reached")

    class FakeProviderManager:
        def get(self, name):
            return FakeProvider()

    class FakeProfiles:
        def get(self, profile_id):
            return _profile()

    monkeypatch.setattr(
        "engines.voice_engine.server.provider_manager",
        FakeProviderManager(),
    )
    monkeypatch.setattr(
        "engines.voice_engine.server.voice_profile_manager",
        FakeProfiles(),
    )
    monkeypatch.setattr(
        "engines.voice_engine.validate_managed_reference",
        lambda filename: None,
    )

    request = SimpleNamespace(
        profile_id="voice-1",
        reference_audio_filename=None,
        text="నమస్కారం",
        generation_settings={"unsupported": 1},
    )

    with pytest.raises(ValueError, match="Unsupported Chatterbox"):
        VoiceEngine.generate(request)
