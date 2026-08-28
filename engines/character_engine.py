import json

from core.server_context import server


class CharacterEngine:

    # =========================================================
    # GET OLLAMA
    # =========================================================

    @staticmethod
    def _provider():

        provider = server.provider_manager.get(
            "ollama"
        )

        if provider is None:

            raise RuntimeError(
                "Ollama provider is not available."
            )

        return provider

    # =========================================================
    # NORMAL CHARACTER
    # =========================================================

    @staticmethod
    def generate(request):

        provider = (
            CharacterEngine._provider()
        )

        prompt = f"""
You are a professional Character Designer
for MATANGI AI STUDIO.

Analyze the user's character idea.

Return ONLY valid JSON.

Do NOT return markdown.

Do NOT return explanations.

Use exactly this JSON structure:

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
    "style": "{request.style}",
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

    # =========================================================
    # MASTER SCRIPT EXTRACTION
    # =========================================================

    @staticmethod
    def extract(request):

        provider = (
            CharacterEngine._provider()
        )

        script = (
            request.script
            if request.script
            else ""
        )

        if not script.strip():

            return {
                "success": False,
                "message":
                    "Master Script is empty."
            }

        prompt = f"""
You are a professional screenplay character analyst
for MATANGI AI STUDIO.

Your ONLY task is to extract characters that already
exist in the supplied Master Script.

This is an EXTRACTION task.

DO NOT creatively rewrite the story.

STRICT RULES:

1. Extract only characters actually present in the script.

2. NEVER invent characters.

3. NEVER add characters because they seem necessary.

4. Preserve the exact names and identities from the script.

5. If the same character appears multiple times,
   return that character only once.

6. Do not create separate characters for different
   scenes if they are the same person.

7. Do not turn unnamed background people into major
   characters.

8. Preserve mythology-specific identities exactly.

9. Do not replace mythology characters.

10. Do not change the story.

11. Do not create new relationships.

12. Do not create new powers.

13. Do not create new costumes.

14. Only extract information supported by the script.

15. If information is not available, use an empty string.

16. Return ONLY valid JSON.

RETURN EXACTLY:

{{
    "characters": [
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
            "style": "{request.style}",
            "negative_prompt": ""
        }}
    ]
}}

LANGUAGE:

{request.language}

MASTER SCRIPT:

{script}
"""

        result = provider.generate(
            prompt,
            validation_type="character_extraction"
        )

        return CharacterEngine._normalize(
            result
        )

    # =========================================================
    # PROFILE EXPANSION
    # =========================================================

    @staticmethod
    def profile(request):

        provider = (
            CharacterEngine._provider()
        )

        character = (
            request.character
            if request.character
            else {}
        )

        prompt = f"""
You are a professional cinematic character
development designer for MATANGI AI STUDIO.

Expand the supplied EXISTING CHARACTER into
a complete production-ready character profile.

IMPORTANT:

The character already exists.

DO NOT create a different character.

Preserve:

- Name
- Identity
- Gender
- Role
- Mythology identity
- Existing powers
- Existing important characteristics

Only expand missing visual information when it
is necessary for a complete production profile.

Return ONLY valid JSON.

Use exactly:

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
    "style": "{request.style}",
    "negative_prompt": ""
}}

EXISTING CHARACTER:

{json.dumps(character, ensure_ascii=False, indent=2)}

MASTER SCRIPT:

{request.master_script}
"""

        result = provider.generate(
            prompt,
            validation_type="character"
        )

        return CharacterEngine._normalize(
            result
        )

    # =========================================================
    # CHARACTER CONCEPTS
    # =========================================================

    @staticmethod
    def concepts(request):

        provider = (
            CharacterEngine._provider()
        )

        character = (
            request.character
            if request.character
            else {}
        )

        prompt = f"""
You are a professional cinematic character
concept designer for MATANGI AI STUDIO.

Create exactly FOUR visual concepts for the
EXISTING character supplied below.

IMPORTANT:

This is NOT character creation.

All four concepts MUST represent the SAME character.

Do NOT change:

- Character identity
- Name
- Gender
- Mythology identity
- Core appearance
- Core costume
- Important accessories
- Existing powers

The concepts may differ in:

- Camera framing
- Pose
- Composition
- Cinematic presentation
- Story presentation

CONCEPT TYPES:

Concept 1:
Facial identity / portrait.

Concept 2:
Full-body character presentation.

Concept 3:
Epic cinematic / heroic presentation.

Concept 4:
Story-appropriate cinematic presentation.

Return ONLY valid JSON.

Use exactly:

{{
    "character_name": "",
    "concepts": [
        {{
            "number": 1,
            "title": "",
            "description": "",
            "image_prompt": ""
        }},
        {{
            "number": 2,
            "title": "",
            "description": "",
            "image_prompt": ""
        }},
        {{
            "number": 3,
            "title": "",
            "description": "",
            "image_prompt": ""
        }},
        {{
            "number": 4,
            "title": "",
            "description": "",
            "image_prompt": ""
        }}
    ]
}}

STYLE:

{request.style}

EXISTING CHARACTER PROFILE:

{json.dumps(character, ensure_ascii=False, indent=2)}
"""

        result = provider.generate(
            prompt,
            validation_type="character_concepts"
        )

        return CharacterEngine._normalize(
            result
        )

    # =========================================================
    # RESPONSE NORMALIZER
    # =========================================================

    @staticmethod
    def _normalize(result):

        if not isinstance(
            result,
            dict
        ):

            return {
                "success": False,
                "message":
                    "Invalid response from Ollama."
            }

        if not result.get(
            "success",
            False
        ):

            return result

        raw_data = result.get(
            "data",
            result.get(
                "output",
                ""
            )
        )

        if isinstance(
            raw_data,
            dict
        ):

            return {
                "success": True,
                "data": raw_data
            }

        text = str(
            raw_data
            if raw_data is not None
            else ""
        ).strip()

        if not text:

            return {
                "success": False,
                "message":
                    "Ollama returned an empty response."
            }

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

        try:

            data = json.loads(
                text
            )

            return {
                "success": True,
                "data": data
            }

        except json.JSONDecodeError:

            return {
                "success": False,
                "message":
                    "Ollama returned invalid JSON.",
                "raw_data":
                    text
            }