from core.server_context import server


class VoiceEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get(

            "kokoro"

        )

        return provider.generate(

            text=request.text,

            voice=request.voice,

            language=request.language

        )