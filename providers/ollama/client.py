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

        prompt

    ):

        return self.client.generate(

            model=model,

            prompt=prompt

        )