import os
from pathlib import Path
import shutil
import tempfile
from threading import Lock
import uuid
import wave

from providers.base.provider import BaseProvider
from config.paths import CHATTERBOX_MODEL_DIR, VOICE_AUDIO
from config.settings import settings
from core.voice_reference_storage import validate_managed_reference


class LocalTeluguTTSProvider(BaseProvider):
    MODEL_ID = "shankarpandala/chatterbox-telugu"
    T3_MODEL = "t3_mtl_te.safetensors"
    ALLOWED_T3_MODELS = {T3_MODEL}
    OUTPUT_FORMAT = "wav"
    LICENSE = "CC-BY-4.0"
    ATTRIBUTION = (
        "Chatterbox Telugu by shankarpandala, based on Resemble AI "
        "Chatterbox."
    )
    REQUIRED_MODEL_FILES = (
        "t3_mtl_te.safetensors",
        "s3gen.pt",
        "ve.pt",
        "grapheme_mtl_merged_expanded_v1.json",
    )
    ALLOWED_SETTINGS = {
        "exaggeration": (0.0, 2.0),
        "cfg_weight": (0.0, 2.0),
        "temperature": (0.05, 2.0),
        "repetition_penalty": (0.5, 2.0),
        "min_p": (0.0, 1.0),
        "top_p": (0.0, 1.0),
    }
    MIN_REFERENCE_SECONDS = 2.0
    MAX_REFERENCE_SECONDS = 10.0

    def __init__(self):
        super().__init__("Local Telugu TTS")
        configured_path = settings.CHATTERBOX_MODEL_PATH
        self.model_path = Path(configured_path) if configured_path else CHATTERBOX_MODEL_DIR
        self.device_setting = settings.CHATTERBOX_DEVICE
        self.t3_model = settings.CHATTERBOX_T3_MODEL
        configured_output_path = settings.CHATTERBOX_OUTPUT_PATH
        self.output_path = (
            Path(configured_output_path)
            if configured_output_path
            else Path(VOICE_AUDIO)
        )
        self._model = None
        self._model_lock = Lock()
        self._state_lock = Lock()
        self._model_state = "not_loaded"
        self._last_load_error = None

    @staticmethod
    def _load_dependencies():
        try:
            import torch
            import chatterbox.mtl_tts as mtl_tts
        except ImportError as error:
            raise RuntimeError(
                "Chatterbox Telugu dependencies are not installed."
            ) from error
        return torch, mtl_tts

    def _resolve_device(self, torch):
        device = self.device_setting.strip().lower()
        if device not in {"auto", "cuda", "cpu", "mps"}:
            raise RuntimeError(
                "CHATTERBOX_DEVICE must be one of: auto, cuda, cpu, mps."
            )
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable for Chatterbox Telugu.")
        if device == "mps":
            if not hasattr(torch.backends, "mps") or not torch.backends.mps.is_available():
                raise RuntimeError("MPS is unavailable for Chatterbox Telugu.")
        return device

    def _check_model_files(self):
        if not self.model_path.is_dir():
            raise RuntimeError(
                "Chatterbox Telugu model directory is unavailable."
            )
        missing = [
            filename
            for filename in self.REQUIRED_MODEL_FILES
            if not (self.model_path / filename).is_file()
        ]
        if missing:
            raise RuntimeError(
                "Chatterbox Telugu model files are missing: "
                + ", ".join(missing)
            )

    def _set_model_state(self, state, error=None):
        with self._state_lock:
            self._model_state = state
            self._last_load_error = error

    def _get_model_state(self):
        with self._state_lock:
            return self._model_state, self._last_load_error

    def readiness(self):
        dependencies_available = False
        model_files_present = False
        device_available = False
        selected_device = None
        diagnostic = "Chatterbox Telugu generation is ready to be attempted."

        try:
            torch, _ = self._load_dependencies()
            dependencies_available = True
        except ImportError:
            diagnostic = "Chatterbox Telugu dependencies are unavailable."
            torch = None

        if dependencies_available:
            try:
                self._check_model_files()
                model_files_present = True
            except RuntimeError:
                diagnostic = "Chatterbox Telugu model checkpoint files are unavailable."

            try:
                selected_device = self._resolve_device(torch)
                device_available = True
            except (RuntimeError, AttributeError):
                diagnostic = "The configured Chatterbox device is unavailable."

        model_state, load_error = self._get_model_state()
        if model_state == "failed" and load_error:
            diagnostic = load_error

        generation_available = (
            dependencies_available
            and model_files_present
            and device_available
            and model_state in {"not_loaded", "loaded"}
        )
        return {
            "server_connected": True,
            "server_healthy": True,
            "provider_registered": True,
            "dependencies_available": dependencies_available,
            "model_files_present": model_files_present,
            "device_available": device_available,
            "selected_device": selected_device,
            "model_state": model_state,
            "generation_available": generation_available,
            "message": diagnostic,
        }

    def _enable_telugu_language(self, mtl_tts, model_instance):
        t3_model = getattr(self, "t3_model", self.T3_MODEL)
        if t3_model not in self.ALLOWED_T3_MODELS:
            raise RuntimeError(
                "Unsupported Chatterbox Telugu checkpoint: "
                f"{t3_model}"
            )
        try:
            vocabulary = model_instance.tokenizer.tokenizer.get_vocab()
        except AttributeError as error:
            raise RuntimeError(
                "Unable to verify Telugu tokenizer support."
            ) from error
        if "[te]" not in vocabulary:
            raise RuntimeError(
                "The configured Chatterbox tokenizer does not contain [te]."
            )
        mtl_tts.SUPPORTED_LANGUAGES.setdefault("te", "Telugu")

    def _load_model(self, torch, mtl_tts):
        if self._model is not None:
            self._set_model_state("loaded")
            return self._model
        self._set_model_state("loading")
        if self.t3_model not in self.ALLOWED_T3_MODELS:
            self._set_model_state(
                "failed",
                "The configured Chatterbox Telugu checkpoint is unsupported.",
            )
            raise RuntimeError(
                "Unsupported Chatterbox Telugu checkpoint: "
                f"{self.t3_model}"
            )
        try:
            self._check_model_files()
            device = self._resolve_device(torch)
            from providers.voice.chatterbox_telugu_compat import load_telugu_model

            self._model = load_telugu_model(
                self.model_path,
                device=device,
                checkpoint_name=self.t3_model,
            )
            self._enable_telugu_language(mtl_tts, self._model)
        except Exception as error:
            if self._is_oom(torch, error):
                self._set_model_state(
                    "failed",
                    "Chatterbox Telugu model loading ran out of GPU memory.",
                )
                raise RuntimeError(
                    "Chatterbox Telugu model loading ran out of GPU memory."
                ) from error
            self._set_model_state(
                "failed",
                "Unable to load the Chatterbox Telugu model.",
            )
            raise RuntimeError(
                "Unable to load the Chatterbox Telugu model."
            ) from error
        self._set_model_state("loaded")
        return self._model

    @classmethod
    def _is_oom(cls, torch, error):
        return isinstance(error, torch.cuda.OutOfMemoryError) or (
            "out of memory" in str(error).lower()
        )

    @classmethod
    def _validated_settings(cls, settings_value):
        if settings_value is None:
            return {}
        if not isinstance(settings_value, dict):
            raise ValueError("Voice generation settings must be an object.")
        unknown = set(settings_value) - set(cls.ALLOWED_SETTINGS)
        if unknown:
            raise ValueError(
                "Unsupported Chatterbox generation settings: "
                + ", ".join(sorted(unknown))
            )
        validated = {}
        for name, value in settings_value.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"Chatterbox setting '{name}' must be numeric."
                )
            minimum, maximum = cls.ALLOWED_SETTINGS[name]
            if not minimum <= value <= maximum:
                raise ValueError(
                    f"Chatterbox setting '{name}' must be between "
                    f"{minimum} and {maximum}."
                )
            validated[name] = float(value)
        return validated

    @classmethod
    def validate_generation_settings(cls, settings_value):
        return cls._validated_settings(settings_value)

    @classmethod
    def _stage_reference(cls, filename):
        source = validate_managed_reference(filename)
        if source.suffix.lower() != ".wav":
            raise ValueError(
                "Chatterbox Telugu requires a WAV reference audio file."
            )

        temporary_path = None
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            source_fd = os.open(source, flags)
            with os.fdopen(source_fd, "rb") as source_file:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    suffix=".wav",
                    delete=False,
                ) as target_file:
                    temporary_path = Path(target_file.name)
                    shutil.copyfileobj(source_file, target_file)

            with wave.open(str(temporary_path), "rb") as audio:
                frame_rate = audio.getframerate()
                duration = audio.getnframes() / frame_rate if frame_rate else 0
            if not cls.MIN_REFERENCE_SECONDS <= duration <= cls.MAX_REFERENCE_SECONDS:
                raise ValueError(
                    "Chatterbox reference audio must be between 2 and 10 seconds."
                )
            return temporary_path
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _waveform_array(waveform):
        try:
            array = waveform.detach().cpu().numpy()
        except AttributeError as error:
            raise RuntimeError(
                "Chatterbox returned an unsupported audio value."
            ) from error
        array = array.squeeze()
        if array.ndim != 1 or array.size == 0:
            raise RuntimeError("Chatterbox returned an empty audio waveform.")
        return array

    def _write_output(self, waveform, sample_rate):
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise RuntimeError("Chatterbox returned an invalid sample rate.")
        output_dir = self.output_path
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"voice_{uuid.uuid4().hex}.wav"
        final_path = output_dir / filename
        temporary_path = None
        try:
            import soundfile as sf

            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=".wav",
                dir=output_dir,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
            sf.write(
                str(temporary_path),
                waveform,
                sample_rate,
                format="WAV",
                subtype="PCM_16",
            )
            with temporary_path.open("rb") as output:
                os.fsync(output.fileno())
            os.replace(temporary_path, final_path)
            temporary_path = None
            size_bytes = final_path.stat().st_size
            if size_bytes <= 0:
                raise RuntimeError("Generated audio file is empty.")
            duration = len(waveform) / sample_rate
            return {
                "success": True,
                "provider": self.name,
                "model": self.MODEL_ID,
                "profile_id": self._active_profile_id,
                "filename": filename,
                "audio_url": f"/audio/{filename}",
                "format": self.OUTPUT_FORMAT,
                "sample_rate": sample_rate,
                "duration": duration,
                "size_bytes": size_bytes,
                "license": self.LICENSE,
                "attribution": self.ATTRIBUTION,
                "watermarked": True,
            }
        except ImportError as error:
            raise RuntimeError(
                "The soundfile dependency is required for WAV output."
            ) from error
        except OSError as error:
            raise RuntimeError(
                "Unable to write generated Telugu audio."
            ) from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def generate_voice(
        self,
        *,
        text,
        profile_id=None,
        reference_audio_filename=None,
        reference_transcript="",
        language="Telugu",
        model=MODEL_ID,
        generation_settings=None,
        **kwargs,
    ):
        del reference_transcript, kwargs
        if model != self.MODEL_ID:
            raise ValueError(
                f"Unsupported local voice model: {model}"
            )
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Voice text cannot be empty.")
        if str(language).strip().lower() not in {"telugu", "te"}:
            raise ValueError(
                "Chatterbox Telugu requires a Telugu voice profile."
            )

        settings_value = self._validated_settings(generation_settings)
        with self._model_lock:
            reference_path = None
            if reference_audio_filename is not None:
                reference_path = self._stage_reference(
                    reference_audio_filename
                )
            self._active_profile_id = profile_id
            try:
                torch, mtl_tts = self._load_dependencies()
                model_instance = self._load_model(torch, mtl_tts)
                try:
                    waveform = model_instance.generate(
                        text=text,
                        language_id="te",
                        audio_prompt_path=(
                            str(reference_path)
                            if reference_path is not None
                            else None
                        ),
                        **settings_value,
                    )
                except Exception as error:
                    if self._is_oom(torch, error):
                        raise RuntimeError(
                            "Chatterbox Telugu inference ran out of GPU memory."
                        ) from error
                    raise RuntimeError(
                        "Chatterbox Telugu inference failed."
                    ) from error
                return self._write_output(
                    self._waveform_array(waveform),
                    int(model_instance.sr),
                )
            finally:
                if reference_path is not None:
                    reference_path.unlink(missing_ok=True)
                self._active_profile_id = None

    def generate(self, *args, **kwargs):
        return self.generate_voice(*args, **kwargs)

    def health(self):
        return {
            "provider": self.name,
            "model": self.MODEL_ID,
            "status": self._get_model_state()[0],
            "model_path": str(self.model_path),
            "license": self.LICENSE,
            "watermarked": True,
        }
