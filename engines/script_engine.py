from core.server_context import server


class ScriptEngine:

    @staticmethod
    def generate(

        title,

        description,

        style="Cinematic",

        language="English"

    ):

        provider = server.provider_manager.get(

            "ollama"

        )

        prompt = f"""
You are a professional cinematic screenplay writer.

Create a detailed screenplay based on the information below.

Title:
{title}

Description:
{description}

Style:
{style}

Language:
{language}

Requirements:

1. Write the screenplay in the requested language.
2. Structure the screenplay into clear scenes.
3. Include scene descriptions.
4. Include character actions and dialogue where appropriate.
5. Maintain cinematic storytelling.
6. Respect the requested visual style.
7. Do not explain your process.
8. Return ONLY the screenplay.
"""

        result = provider.generate(

            prompt,

            validate_prompt=False

        )

        if not result.get("success"):

            return result

        return {

            "success": True,

            "provider": "Ollama",

            "data": result.get(

                "output",

                ""

            )

        }
