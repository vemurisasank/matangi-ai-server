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
        validate_prompt=False,
        validation_type=None,
        model=settings.TEXT_MODEL
    ):

        response = self.client.generate(
            model,
            prompt,
            json_mode=(
                validate_prompt
                or validation_type is not None
            )
        )

        raw_output = response["response"]

        # --------------------------------------------------
        # RAW TEXT MODE
        # --------------------------------------------------

        if not validate_prompt and validation_type is None:

            return {
                "success": True,
                "provider": "Ollama",
                "output": raw_output
            }

        # --------------------------------------------------
        # PARSE JSON
        # --------------------------------------------------

        parsed = ResponseParser.parse(
            raw_output
        )

        # --------------------------------------------------
        # PROMPT VALIDATION
        # --------------------------------------------------

        if validate_prompt:

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

        # --------------------------------------------------
        # SCENE VALIDATION
        # --------------------------------------------------

        elif validation_type == "scene":

            if not SchemaValidator.validate_scene(
                parsed
            ):

                return {
                    "success": False,
                    "provider": "Ollama",
                    "message": "Invalid Scene Response",
                    "output": parsed
                }

        # --------------------------------------------------
        # CHARACTER VALIDATION
        # --------------------------------------------------

        elif validation_type == "character":

            if not SchemaValidator.validate_character(
                parsed
            ):

                return {
                    "success": False,
                    "provider": "Ollama",
                    "message": "Invalid Character Response",
                    "output": parsed
                }

        # --------------------------------------------------
        # FINAL RESPONSE
        # --------------------------------------------------

        return {
            "success": True,
            "provider": "Ollama",
            "output": parsed
        }
