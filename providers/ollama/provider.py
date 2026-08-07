from providers.ollama.client import OllamaClient
from core.response_parser import ResponseParser
from core.logger import Logger
from core.schema_validator import SchemaValidator
from core.response_normalizer import ResponseNormalizer
from config.settings import settings
from providers.base.provider import BaseProvider

class OllamaProvider(BaseProvider):

    def __init__(self):

        super().__init__("Ollama")

        Logger.info("Initializing Ollama Provider")

        self.client = OllamaClient()

    def generate(

        self,

        prompt,

        model=settings.TEXT_MODEL

    ):

        response = self.client.generate(

            model,

            prompt

        )

        parsed = ResponseParser.parse(

            response["response"]

        )

        if SchemaValidator.validate_prompt(

            parsed

        ):

            parsed = ResponseNormalizer.normalize_prompt(

                parsed

            )

        else:

            return {

                "success": False,

                "provider": "Ollama",

                "message": "Invalid AI Response",

                "output": parsed

            }

        return {

            "success": True,

            "provider": "Ollama",

            "output": parsed

        }