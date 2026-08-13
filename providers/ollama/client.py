from ollama import Client
from config.settings import settings


class OllamaClient:

    def __init__(self):

        self.client = Client(

            host=settings.OLLAMA_HOST

        )

    def generate(

        self,

        model,

        prompt,

        json_mode=False

    ):

        options = {}

        if json_mode:

            options["format"] = "json"

        return self.client.generate(

            model=model,

            prompt=prompt,

            **options

        )
