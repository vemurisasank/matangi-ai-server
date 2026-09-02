from core.server_context import server


class ImageEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get("comfyui")

        return provider.generate(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            seed=request.seed,
            reference_images=request.reference_images
        )