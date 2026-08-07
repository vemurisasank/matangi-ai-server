from core.server_context import server


class VideoEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get(

            "wan"

        )

        return provider.generate(

            prompt=request.prompt,

            duration=request.duration,

            fps=request.fps

        )