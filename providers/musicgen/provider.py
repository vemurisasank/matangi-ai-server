import base64
import json
import os
import re
import uuid

import requests

from providers.base.provider import BaseProvider
from core.logger import Logger


class MusicGenProvider(BaseProvider):
    """
    Local ACE-Step music generation provider.

    The existing Matangi model name is kept as "musicgen"
    so the existing MusicEngine/API does not need to change.
    """

    def __init__(self):
        super().__init__("ACE-Step MusicGen")

        self.server_url = os.getenv(
            "ACESTEP_LOCAL_URL",
            "http://127.0.0.1:8001"
        ).rstrip("/")

        self.output_dir = os.getenv(
            "MATANGI_AUDIO_OUTPUT",
            "/workspace/matangi-ai-server/outputs/audio"
        )

        os.makedirs(self.output_dir, exist_ok=True)

        Logger.info(
            f"ACE-Step Music Provider initialized: {self.server_url}"
        )

    def generate(
        self,
        prompt: str,
        duration: int = 30,
        style: str = "Cinematic",
    ):
        if not prompt or not prompt.strip():
            raise ValueError("Music prompt cannot be empty.")

        duration = max(1, min(int(duration), 600))

        caption = prompt.strip()

        if style and style.strip():
            caption = f"{style.strip()} music, {caption}"

        request_body = {
            "model": "acestep/acestep-v15-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": caption,
                }
            ],
            "modalities": ["audio"],
            "stream": False,
            "task_type": "text2music",
            "thinking": True,
            "temperature": 0.85,
            "top_p": 0.9,
            "use_cot_caption": True,
            "use_cot_language": True,
            "audio_config": {
                "format": "wav",
                "vocal_language": "en",
                "instrumental": True,
                "duration": duration,
            },
        }

        url = f"{self.server_url}/v1/chat/completions"

        Logger.info(
            f"ACE-Step music generation started: "
            f"duration={duration}s"
        )

        try:
            response = requests.post(
                url,
                json=request_body,
                timeout=900,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Could not connect to ACE-Step at {self.server_url}: {exc}"
            ) from exc

        if response.status_code != 200:
            raise RuntimeError(
                f"ACE-Step API error {response.status_code}: "
                f"{response.text[:2000]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"ACE-Step returned invalid JSON: "
                f"{response.text[:1000]}"
            ) from exc

        try:
            audio_items = data["choices"][0]["message"]["audio"]
            audio_url = audio_items[0]["audio_url"]["url"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "ACE-Step response did not contain audio data."
            ) from exc

        if not isinstance(audio_url, str):
            raise RuntimeError(
                "ACE-Step audio URL is not a string."
            )

        if audio_url.startswith("data:"):
            try:
                audio_b64 = audio_url.split(",", 1)[1]
            except IndexError as exc:
                raise RuntimeError(
                    "Invalid ACE-Step audio data URL."
                ) from exc
        else:
            audio_b64 = audio_url

        audio_b64 = re.sub(r"\s+", "", audio_b64)

        try:
            audio_bytes = base64.b64decode(
                audio_b64,
                validate=True,
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to decode ACE-Step audio."
            ) from exc

        filename = f"music_{uuid.uuid4().hex[:12]}.wav"
        output_path = os.path.join(
            self.output_dir,
            filename,
        )

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        Logger.info(
            f"ACE-Step music generated successfully: {output_path}"
        )

        return {
            "success": True,
            "provider": "ACE-Step",
            "model": "acestep-v15-turbo",
            "filename": filename,
            "path": output_path,
            "audio_url": f"/audio/{filename}",
            "format": "wav",
            "duration": duration,
            "style": style,
            "size_bytes": len(audio_bytes),
        }
