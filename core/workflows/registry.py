class WorkflowRegistry:

    WORKFLOWS = {

        "text_to_image": "flux_text_to_image",

        "image_to_image": "flux_image_to_image",

        "upscale": "flux_upscale",

        "inpaint": "flux_inpaint",

        "controlnet": "flux_controlnet",

        "z_image_text_to_image_api.json": "z_image_text_to_image_api.json"

    }

    @staticmethod
    def get(name):

        return WorkflowRegistry.WORKFLOWS.get(name)
