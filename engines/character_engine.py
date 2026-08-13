from core.server_context import server


class CharacterEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get(
            "ollama"
        )

        prompt = f"""
You are a professional Character Designer.

Analyze the user's idea and return ONLY valid JSON.

Do NOT return markdown.

Do NOT return explanations.

Use this exact JSON structure:

{{
    "name": "",
    "role": "",
    "gender": "",
    "age": "",
    "appearance": "",
    "costume": "",
    "accessories": "",
    "hairstyle": "",
    "face": "",
    "eyes": "",
    "body": "",
    "personality": "",
    "powers": "",
    "style": "",
    "negative_prompt": ""
}}

STYLE:

{request.style}

CHARACTER DESCRIPTION:

{request.description}
"""

        return provider.generate(
            prompt,
            validation_type="character"
        )
