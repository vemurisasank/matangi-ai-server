from core.server_context import server


class ThreeDEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get("comfyui")

        return provider.generate_3d(
            image=request.image,
            asset_id=request.asset_id,
            resolution=request.resolution,
            batch_size=request.batch_size,
            seed=request.seed,
            steps=request.steps,
            cfg=request.cfg,
            octree_resolution=request.octree_resolution,
            threshold=request.threshold
        )
