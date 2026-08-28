from ollama import Client

from config.settings import settings


class OllamaClient:

    def __init__(self):

        self.client = Client(
            host=settings.OLLAMA_HOST
        )

    # ---------------------------------------------------------
    # GENERATE
    # ---------------------------------------------------------

    def generate(
        self,
        model,
        prompt,
        json_mode=False,
        num_predict=None,
        temperature=None,
        context_length=None
    ):

        # -----------------------------------------------------
        # DEFAULT GENERATION LIMITS
        # -----------------------------------------------------

        if num_predict is None:

            if json_mode:

                # Structured responses such as:
                # scenes, characters, prompts, etc.
                num_predict = 4096

            else:

                # Normal text generation.
                num_predict = 4096

        # -----------------------------------------------------
        # OPTIONS
        # -----------------------------------------------------

        options = {

            "num_predict": num_predict

        }

        if temperature is not None:

            options["temperature"] = temperature

        if context_length is not None:

            options["num_ctx"] = context_length

        # -----------------------------------------------------
        # JSON MODE
        # -----------------------------------------------------

        if json_mode:

            options["format"] = "json"

        # -----------------------------------------------------
        # GENERATE
        # -----------------------------------------------------

        return self.client.generate(

            model=model,

            prompt=prompt,

            options=options

        )