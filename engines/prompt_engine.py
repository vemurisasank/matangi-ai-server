from core.server_context import server

from core.prompt_builder import PromptBuilder


class PromptEngine:

    @staticmethod
    def generate(

        request

    ):

        provider = server.provider_manager.get(

            "ollama"

        )

        prompt = PromptBuilder.build_scene_prompt(

            request.script,

            request.style,

            request.language,

            request.scene_count

        )

        return provider.generate(

            prompt

        )