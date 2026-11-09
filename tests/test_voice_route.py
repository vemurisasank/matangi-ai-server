import json
from types import SimpleNamespace

from api.routes import voice


def test_voice_route_returns_consistent_provider_failure(monkeypatch):
    monkeypatch.setattr(
        voice.VoiceEngine,
        "generate",
        lambda request: {
            "success": False,
            "error": "Chatterbox Telugu inference failed.",
        },
    )

    response = voice.generate_voice(SimpleNamespace())

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "success": False,
        "message": "Chatterbox Telugu inference failed.",
        "data": None,
    }


def test_voice_route_returns_bad_request_for_validation_error(monkeypatch):
    monkeypatch.setattr(
        voice.VoiceEngine,
        "generate",
        lambda request: (_ for _ in ()).throw(
            ValueError("Unsupported Chatterbox generation settings.")
        ),
    )

    response = voice.generate_voice(SimpleNamespace())

    assert response.status_code == 400
    assert json.loads(response.body)["success"] is False


def test_readiness_route_uses_registered_provider(monkeypatch):
    readiness = {
        "server_connected": True,
        "server_healthy": True,
        "provider_registered": True,
        "dependencies_available": True,
        "model_files_present": True,
        "device_available": True,
        "selected_device": "cuda",
        "model_state": "not_loaded",
        "generation_available": True,
        "message": "ready",
    }

    class FakeProvider:
        def readiness(self):
            return readiness

    class FakeManager:
        def get(self, name):
            assert name == "local-tts"
            return FakeProvider()

    monkeypatch.setattr(voice.server, "provider_manager", FakeManager())

    response = voice.voice_readiness()

    assert response["success"] is True
    assert response["data"] == readiness


def test_readiness_route_reports_missing_provider(monkeypatch):
    class FakeManager:
        def get(self, name):
            raise ValueError("not registered")

    monkeypatch.setattr(voice.server, "provider_manager", FakeManager())

    response = voice.voice_readiness()

    assert response.status_code == 503
    assert json.loads(response.body)["success"] is False
