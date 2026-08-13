from core.server_context import server


class VideoEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get(
            "comfyui"
        )

        return provider.generate_video(
            prompt=request.prompt,
            duration=request.duration,
            fps=request.fps,
            width=request.width,
            height=request.height,
            reference_image=request.reference_image
        )
