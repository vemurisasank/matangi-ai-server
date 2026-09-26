from core.server_context import server
from core.reference_package_builder import ReferencePackageBuilder


class ImageEngine:

    @staticmethod
    def prepare_qwen_request(
        request,
        scene,
        characters=None,
        environments=None,
        props=None
    ):
        """Prepare an explicit Qwen request with scene-derived references."""
        requested_model = getattr(request, "model", None)

        if requested_model == "qwen-image-text-to-image":
            if hasattr(request, "model_copy"):
                prepared_request = request.model_copy()
            else:
                prepared_request = request.copy()

            prepared_request.model = requested_model
            prepared_request.reference_images = []
            return prepared_request

        package = ReferencePackageBuilder().build(
            scene=scene,
            characters=characters,
            environments=environments,
            props=props
        )

        reference_images = [
            {"filename": reference}
            for reference in package["all_references"]
        ]

        if hasattr(request, "model_copy"):
            prepared_request = request.model_copy()
        else:
            prepared_request = request.copy()

        prepared_request.model = requested_model or "qwen-image-edit-2511"
        prepared_request.reference_images = reference_images

        return prepared_request

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get("comfyui")

        return provider.generate(
            prompt=request.prompt,
            negative_prompt=getattr(request, "negative_prompt", ""),
            width=request.width,
            height=request.height,
            seed=request.seed,
            reference_images=request.reference_images,
            steps=request.steps,
            cfg=request.cfg,
            sampler=request.sampler,
            scheduler=request.scheduler,
            model=request.model
        )