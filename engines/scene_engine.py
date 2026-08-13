from core.server_context import server


class SceneEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get(
            "ollama"
        )

        prompt = f"""
You are an expert screenplay writer.

Split the screenplay into logical movie scenes.

Return ONLY valid JSON.

Do NOT return markdown.

Do NOT return explanations.

Use this exact JSON structure:

{{
    "scenes": [
        {{
            "number": 1,
            "title": "Opening Scene",
            "script": "Scene description...",
            "duration": 10
        }}
    ]
}}

SCREENPLAY:

{request.script}
"""

        return provider.generate(
            prompt,
            validation_type="scene"
        )
