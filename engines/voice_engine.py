from core.server_context import server


class VoiceEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get(
            "comfyui"
        )

        return provider.generate_voice(

            text=request.text,

            voice=request.voice,

            language=request.language

        )
