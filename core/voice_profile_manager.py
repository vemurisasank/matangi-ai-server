import json
import os
import tempfile
from pathlib import Path
from threading import RLock

from config.paths import OUTPUTS
from core.logger import Logger
from models.voice_profile import VoiceProfile


class VoiceProfileManager:
    def __init__(self, storage_path=None):
        self.storage_path = Path(
            storage_path or OUTPUTS / "voice_profiles.json"
        )
        self._lock = RLock()
        self.profiles: dict[str, VoiceProfile] = {}
        self._load()

    @staticmethod
    def _serialize(profile):
        return {
            "id": profile.id,
            "character_id": profile.character_id,
            "reference_audio_filename": profile.reference_audio_filename,
            "reference_transcript": profile.reference_transcript,
            "language": profile.language,
            "model": profile.model,
            "generation_settings": profile.generation_settings,
            "created_on": profile.created_on,
            "updated_on": profile.updated_on,
        }

    @staticmethod
    def _from_record(record):
        return VoiceProfile(
            id=record["id"],
            character_id=record.get("character_id", ""),
            reference_audio_filename=record["reference_audio_filename"],
            reference_transcript=record.get("reference_transcript", ""),
            language=record.get("language", "Telugu"),
            model=record.get(
                "model",
                "shankarpandala/chatterbox-telugu"
            ),
            generation_settings=record.get("generation_settings", {}),
            created_on=record.get("created_on", ""),
            updated_on=record.get("updated_on", ""),
        )

    def _load(self):
        if not self.storage_path.exists():
            return
        try:
            with self.storage_path.open("r", encoding="utf-8") as file:
                records = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Unable to load voice profiles from {self.storage_path}"
            ) from error
        if not isinstance(records, list):
            raise RuntimeError(
                f"Voice profiles must be a list: {self.storage_path}"
            )
        for record in records:
            if not isinstance(record, dict) or not record.get("id"):
                raise RuntimeError(
                    f"Invalid voice profile record: {self.storage_path}"
                )
            self.profiles[record["id"]] = self._from_record(record)

    def _save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.storage_path.parent,
                prefix=f".{self.storage_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                json.dump(
                    [
                        self._serialize(profile)
                        for profile in self.profiles.values()
                    ],
                    file,
                    ensure_ascii=False,
                )
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.storage_path)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    def create(self, profile):
        with self._lock:
            if profile.id in self.profiles:
                raise ValueError(f"Voice profile already exists: {profile.id}")
            self.profiles[profile.id] = profile
            self._save()
        Logger.info(f"Voice Profile Created: {profile.id}")
        return profile

    def get(self, profile_id):
        return self.profiles.get(profile_id)

    def get_all(self):
        return list(self.profiles.values())

    def update(self, profile_id, **changes):
        with self._lock:
            profile = self.profiles.get(profile_id)
            if profile is None:
                return None
            for field, value in changes.items():
                if value is not None:
                    setattr(profile, field, value)
            self._save()
        Logger.info(f"Voice Profile Updated: {profile_id}")
        return profile
