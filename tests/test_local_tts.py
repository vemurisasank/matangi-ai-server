from pathlib import Path
import types
import wave

import pytest

from providers.voice import chatterbox_telugu_compat
from providers.voice.local_tts import LocalTeluguTTSProvider


class _FakeTokenizer:
    def __init__(self, vocabulary):
        self.tokenizer = types.SimpleNamespace(get_vocab=lambda: vocabulary)


class _FakeModel:
    sr = 24000

    def __init__(self, vocabulary=None):
        self.tokenizer = _FakeTokenizer(vocabulary or {"[te]": 2520})


def _write_wav(path, seconds):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(b"\x00\x00" * int(24000 * seconds))


@pytest.mark.parametrize("seconds", [2, 10])
def test_reference_duration_boundaries_are_accepted(
    tmp_path, monkeypatch, seconds
):
    reference = tmp_path / "reference.wav"
    _write_wav(reference, seconds)
    monkeypatch.setattr(
        "providers.voice.local_tts.validate_managed_reference",
        lambda filename: reference,
    )

    staged = LocalTeluguTTSProvider._stage_reference("reference.wav")

    assert staged.is_file()
    staged.unlink()


@pytest.mark.parametrize("seconds", [1.99, 10.01])
def test_reference_duration_outside_bounds_is_rejected(
    tmp_path, monkeypatch, seconds
):
    reference = tmp_path / "reference.wav"
    _write_wav(reference, seconds)
    monkeypatch.setattr(
        "providers.voice.local_tts.validate_managed_reference",
        lambda filename: reference,
    )

    with pytest.raises(ValueError, match="between 2 and 10 seconds"):
        LocalTeluguTTSProvider._stage_reference("reference.wav")


def test_invalid_reference_wav_is_rejected(tmp_path, monkeypatch):
    reference = tmp_path / "reference.wav"
    reference.write_bytes(b"not a wav")
    monkeypatch.setattr(
        "providers.voice.local_tts.validate_managed_reference",
        lambda filename: reference,
    )

    with pytest.raises((ValueError, wave.Error, OSError)):
        LocalTeluguTTSProvider._stage_reference("reference.wav")


def test_telugu_language_adapter_requires_tokenizer_tag():
    provider = LocalTeluguTTSProvider()
    module = types.SimpleNamespace(SUPPORTED_LANGUAGES={"en": "English"})

    provider._enable_telugu_language(module, _FakeModel())

    assert module.SUPPORTED_LANGUAGES["te"] == "Telugu"


def test_telugu_language_adapter_rejects_missing_tokenizer_tag():
    provider = LocalTeluguTTSProvider()
    module = types.SimpleNamespace(SUPPORTED_LANGUAGES={"en": "English"})

    with pytest.raises(RuntimeError, match=r"does not contain \[te\]"):
        provider._enable_telugu_language(module, _FakeModel({"[en]": 708}))


def test_provider_is_lazy():
    provider = LocalTeluguTTSProvider()

    assert provider._model is None


def test_readiness_reports_not_loaded_and_does_not_load_model(monkeypatch):
    provider = LocalTeluguTTSProvider()
    calls = []

    class FakeTorch:
        class cuda:
            @staticmethod
            def is_available():
                return False

    monkeypatch.setattr(
        provider,
        "_load_dependencies",
        lambda: (FakeTorch, types.SimpleNamespace()),
    )
    monkeypatch.setattr(provider, "_check_model_files", lambda: None)
    monkeypatch.setattr(
        provider,
        "_load_model",
        lambda *args: calls.append(True),
    )

    readiness = provider.readiness()

    assert readiness["model_state"] == "not_loaded"
    assert readiness["generation_available"] is True
    assert readiness["selected_device"] == "cpu"
    assert calls == []


def test_readiness_reports_loaded_model():
    provider = LocalTeluguTTSProvider()
    provider._model = object()
    provider._set_model_state("loaded")

    readiness = provider.readiness()

    assert readiness["model_state"] == "loaded"


def test_readiness_reports_loading_state():
    provider = LocalTeluguTTSProvider()
    provider._set_model_state("loading")

    readiness = provider.readiness()

    assert readiness["model_state"] == "loading"
    assert readiness["generation_available"] is False


def test_readiness_reports_failed_model_state():
    provider = LocalTeluguTTSProvider()
    provider._set_model_state("failed", "Unable to load the Chatterbox Telugu model.")

    readiness = provider.readiness()

    assert readiness["model_state"] == "failed"
    assert readiness["generation_available"] is False
    assert readiness["message"] == "Unable to load the Chatterbox Telugu model."


def test_readiness_reports_missing_dependencies(monkeypatch):
    provider = LocalTeluguTTSProvider()
    monkeypatch.setattr(
        provider,
        "_load_dependencies",
        lambda: (_ for _ in ()).throw(ImportError("missing")),
    )

    readiness = provider.readiness()

    assert readiness["dependencies_available"] is False
    assert readiness["generation_available"] is False


def test_readiness_reports_missing_model_files(monkeypatch):
    provider = LocalTeluguTTSProvider()
    fake_torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(is_available=lambda: False)
    )
    monkeypatch.setattr(
        provider,
        "_load_dependencies",
        lambda: (fake_torch, types.SimpleNamespace()),
    )
    monkeypatch.setattr(
        provider,
        "_check_model_files",
        lambda: (_ for _ in ()).throw(RuntimeError("missing")),
    )

    readiness = provider.readiness()

    assert readiness["model_files_present"] is False
    assert readiness["generation_available"] is False


def test_readiness_reports_unavailable_device(monkeypatch):
    provider = LocalTeluguTTSProvider()
    monkeypatch.setattr(
        provider,
        "_load_dependencies",
        lambda: (types.SimpleNamespace(), types.SimpleNamespace()),
    )
    monkeypatch.setattr(provider, "_check_model_files", lambda: None)
    monkeypatch.setattr(
        provider,
        "_resolve_device",
        lambda torch: (_ for _ in ()).throw(RuntimeError("unavailable")),
    )

    readiness = provider.readiness()

    assert readiness["device_available"] is False
    assert readiness["generation_available"] is False


def test_model_initialization_uses_telugu_compat_loader(tmp_path, monkeypatch):
    provider = LocalTeluguTTSProvider()
    provider.model_path = tmp_path
    for filename in provider.REQUIRED_MODEL_FILES:
        (tmp_path / filename).touch()

    class FakeTorch:
        class cuda:
            @staticmethod
            def is_available():
                return False

    module = types.SimpleNamespace(
        SUPPORTED_LANGUAGES={"en": "English"},
    )
    calls = {}

    def fake_loader(path, device, checkpoint_name):
        calls.update(
            path=path,
            device=device,
            checkpoint_name=checkpoint_name,
        )
        return _FakeModel()

    monkeypatch.setattr(
        "providers.voice.chatterbox_telugu_compat.load_telugu_model",
        fake_loader,
    )
    monkeypatch.setattr(provider, "_check_model_files", lambda: None)

    model = provider._load_model(FakeTorch, module)

    assert model is provider._model
    assert provider.readiness()["model_state"] == "loaded"
    assert calls == {
        "path": tmp_path,
        "device": "cpu",
        "checkpoint_name": "t3_mtl_te.safetensors",
    }
    assert module.SUPPORTED_LANGUAGES["te"] == "Telugu"


def test_telugu_loader_builds_2521_token_model_and_loads_conditionals(
    tmp_path, monkeypatch
):
    for filename in chatterbox_telugu_compat.REQUIRED_MODEL_FILES:
        (tmp_path / filename).touch()
    (tmp_path / "conds.pt").touch()

    class FakeTorch:
        @staticmethod
        def device(name):
            return name

        @staticmethod
        def load(path, map_location=None, weights_only=False):
            assert weights_only is True
            return {"weights": path.name}

    class FakeModule:
        def __init__(self):
            self.moves = []

        def load_state_dict(self, state):
            self.state = state

        def to(self, device):
            self.moves.append(device)
            return self

        def eval(self):
            return self

    class FakeT3Config:
        def __init__(self, text_tokens_dict_size):
            assert text_tokens_dict_size == 2521

    class FakeTokenizer:
        def __init__(self, path):
            self.path = path
            self.tokenizer = types.SimpleNamespace(
                get_vocab=lambda: {"[te]": 2520}
            )

    class FakeConditionals:
        @classmethod
        def load(cls, path, map_location):
            assert path == tmp_path / "conds.pt"
            assert map_location == "cpu"
            return cls()

        def to(self, device):
            assert device == "cpu"
            return self

    fake_t3 = FakeModule()
    fake_s3gen = FakeModule()
    fake_voice_encoder = FakeModule()
    safetensors_calls = []

    def fake_load_safetensors(path):
        safetensors_calls.append(path)
        return {"weights": "t3"}

    class FakeRuntime:
        def __init__(self, t3, s3gen, voice_encoder, tokenizer, device, conds):
            self.components = (t3, s3gen, voice_encoder, tokenizer)
            self.device = device
            self.conds = conds

    monkeypatch.setattr(
        chatterbox_telugu_compat,
        "_load_dependencies",
        lambda: (
            FakeTorch,
            types.SimpleNamespace(
                Conditionals=FakeConditionals,
                ChatterboxMultilingualTTS=FakeRuntime,
            ),
            lambda: fake_s3gen,
            lambda config: fake_t3,
            FakeT3Config,
            FakeTokenizer,
            lambda: fake_voice_encoder,
            fake_load_safetensors,
        ),
    )

    model = chatterbox_telugu_compat.load_telugu_model(
        tmp_path,
        device="cpu",
    )

    assert model.device == "cpu"
    assert model.conds is not None
    assert safetensors_calls == [tmp_path / "t3_mtl_te.safetensors"]
    assert fake_t3.state == {"weights": "t3"}
    assert fake_s3gen.state == {"weights": "s3gen.pt"}
    assert fake_voice_encoder.state == {"weights": "ve.pt"}


def test_telugu_loader_rejects_missing_checkpoint(tmp_path):
    for filename in chatterbox_telugu_compat.REQUIRED_MODEL_FILES:
        if filename != "t3_mtl_te.safetensors":
            (tmp_path / filename).touch()

    with pytest.raises(RuntimeError, match="missing"):
        chatterbox_telugu_compat.load_telugu_model(
            tmp_path,
            device="cpu",
        )


def test_telugu_loader_rejects_wrong_token_id(tmp_path, monkeypatch):
    for filename in chatterbox_telugu_compat.REQUIRED_MODEL_FILES:
        (tmp_path / filename).touch()

    class FakeModule:
        def load_state_dict(self, state):
            pass

        def to(self, device):
            return self

        def eval(self):
            return self

    class FakeTokenizer:
        def __init__(self, path):
            self.tokenizer = types.SimpleNamespace(
                get_vocab=lambda: {"[te]": 123}
            )

    monkeypatch.setattr(
        chatterbox_telugu_compat,
        "_load_dependencies",
        lambda: (
            types.SimpleNamespace(
                device=lambda name: name,
                load=lambda *args, **kwargs: {},
            ),
            types.SimpleNamespace(),
            FakeModule,
            lambda config: FakeModule(),
            lambda **kwargs: None,
            FakeTokenizer,
            FakeModule,
            lambda path: {},
        ),
    )

    with pytest.raises(RuntimeError, match="token ID 2520"):
        chatterbox_telugu_compat.load_telugu_model(tmp_path, device="cpu")


def test_invalid_language_and_reference_fail_before_inference():
    provider = LocalTeluguTTSProvider()

    with pytest.raises(ValueError, match="requires a Telugu"):
        provider.generate_voice(
            text="నమస్కారం",
            profile_id="profile-1",
            reference_audio_filename="missing.wav",
            language="Hindi",
        )

    with pytest.raises(ValueError, match="was not found"):
        provider.generate_voice(
            text="నమస్కారం",
            profile_id="profile-1",
            reference_audio_filename="missing.wav",
            language="Telugu",
        )


def test_reference_conditioned_generation_writes_managed_wav(
    tmp_path, monkeypatch
):
    provider = LocalTeluguTTSProvider()
    provider.output_path = tmp_path / "audio"
    reference_dir = tmp_path / "references"
    reference_dir.mkdir()
    reference = reference_dir / "reference.wav"
    _write_wav(reference, 6)

    fake_waveform = object()

    class FakeTorch:
        class cuda:
            class OutOfMemoryError(Exception):
                pass

            @staticmethod
            def is_available():
                return False

    class FakeModel:
        sr = 24000
        tokenizer = _FakeTokenizer({"[te]": 2520})

        def generate(self, **kwargs):
            assert kwargs["language_id"] == "te"
            assert kwargs["text"] == "నమస్కారం"
            assert Path(kwargs["audio_prompt_path"]).exists()
            return fake_waveform

    module = types.SimpleNamespace(
        SUPPORTED_LANGUAGES={"en": "English"},
    )
    monkeypatch.setattr(
        "providers.voice.chatterbox_telugu_compat.load_telugu_model",
        lambda *args, **kwargs: FakeModel(),
    )
    monkeypatch.setattr(
        provider,
        "_load_dependencies",
        lambda: (FakeTorch, module),
    )
    monkeypatch.setattr(
        provider,
        "_load_model",
        lambda torch, mtl_tts: FakeModel(),
    )
    monkeypatch.setattr(
        "providers.voice.local_tts.validate_managed_reference",
        lambda filename: reference,
    )
    monkeypatch.setattr(
        provider,
        "_waveform_array",
        lambda waveform: [0.0] * 2400,
    )
    monkeypatch.setattr(
        provider,
        "_write_output",
        lambda waveform, sample_rate: {
            "success": True,
            "filename": "voice-test.wav",
            "sample_rate": sample_rate,
        },
    )

    result = provider.generate_voice(
        text="నమస్కారం",
        profile_id="profile-1",
        reference_audio_filename="reference.wav",
        language="Telugu",
    )

    assert result["success"] is True
    assert result["sample_rate"] == 24000


def test_zero_reference_generation_passes_none_without_staging(monkeypatch):
    provider = LocalTeluguTTSProvider()
    calls = {}

    class FakeTorch:
        class cuda:
            class OutOfMemoryError(Exception):
                pass

            @staticmethod
            def is_available():
                return False

    class FakeModel:
        sr = 24000

        def generate(self, **kwargs):
            calls.update(kwargs)
            return object()

    monkeypatch.setattr(
        provider,
        "_stage_reference",
        lambda filename: pytest.fail("zero-reference generation staged audio"),
    )
    monkeypatch.setattr(
        provider,
        "_load_dependencies",
        lambda: (FakeTorch, types.SimpleNamespace()),
    )
    monkeypatch.setattr(provider, "_load_model", lambda torch, module: FakeModel())
    monkeypatch.setattr(
        provider,
        "_waveform_array",
        lambda waveform: [0.0] * 2400,
    )
    monkeypatch.setattr(
        provider,
        "_write_output",
        lambda waveform, sample_rate: {
            "success": True,
            "sample_rate": sample_rate,
        },
    )

    result = provider.generate_voice(
        text="నమస్కారం",
        language="Telugu",
    )

    assert result["success"] is True
    assert calls["audio_prompt_path"] is None
    assert calls["language_id"] == "te"
