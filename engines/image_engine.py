from core.server_context import server


class ImageEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get("comfyui")

        return provider.generate(
            request.prompt,
            request.width,
            request.height,
            request.seed
        )
