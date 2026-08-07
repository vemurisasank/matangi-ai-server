from core.server_context import server


class MusicEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get(

            "musicgen"

        )

        return provider.generate(

            prompt=request.prompt,

            duration=request.duration

        )