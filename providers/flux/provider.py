from core.logger import Logger


class FluxProvider:

    def __init__(self):

        Logger.info(

            "Initializing FLUX Provider"

        )

    def generate(

        self,

        prompt,

        width,

        height,

        seed

    ):

        Logger.info(

            f"Generating Image : {prompt}"

        )

        return {

            "success": True,

            "provider": "FLUX",

            "image": "",

            "prompt": prompt,

            "width": width,

            "height": height,

            "seed": seed

        }