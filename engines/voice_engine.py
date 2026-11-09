from core.server_context import server
from core.voice_reference_storage import validate_managed_reference


class VoiceEngine:

    @staticmethod
    def generate(request):

        if not request.profile_id and request.reference_audio_filename:
            raise ValueError(
                "A voice profile is required for reference audio generation."
            )

        if request.profile_id:
            profile = server.voice_profile_manager.get(request.profile_id)
            if profile is None:
                raise ValueError("Voice profile was not found.")

            validate_managed_reference(
                profile.reference_audio_filename
            )
            provider = server.provider_manager.get("local-tts")
            request_settings = request.generation_settings or {}
            generation_settings = {
                **profile.generation_settings,
                **request_settings,
            }
            generation_settings = provider.validate_generation_settings(
                generation_settings
            )
            return provider.generate_voice(
                text=request.text,
                profile_id=profile.id,
                reference_audio_filename=profile.reference_audio_filename,
                reference_transcript=profile.reference_transcript,
                language=profile.language,
                model=profile.model,
                generation_settings=generation_settings,
            )

        if request.language.strip().lower() == "telugu":
            provider = server.provider_manager.get("local-tts")
            return provider.generate_voice(
                text=request.text,
                profile_id=None,
                reference_audio_filename=None,
                voice=request.voice,
                language=request.language,
                speed=request.speed,
                generation_settings=request.generation_settings,
            )

        provider = server.provider_manager.get("comfyui")
        return provider.generate_voice(
            text=request.text,
            voice=request.voice,
            language=request.language,
        )
