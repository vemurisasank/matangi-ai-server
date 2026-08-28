import json

from core.server_context import server


class EnvironmentEngine:

    # =========================================================
    # GET OLLAMA PROVIDER
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
    # NORMAL ENVIRONMENT GENERATION
    # =========================================================

    @staticmethod
    def generate(request):

        provider = EnvironmentEngine._provider()

        prompt = f"""
You are a professional cinematic environment
designer for MATANGI AI STUDIO.

Analyze the user's environment idea.

Return ONLY valid JSON.

Do NOT return markdown.

Do NOT return explanations.

Use exactly this structure:

{{
    "name": "",
    "type": "",
    "description": "",
    "location": "",
    "time_of_day": "",
    "weather": "",
    "terrain": "",
    "architecture": "",
    "materials": "",
    "geography": "",
    "vegetation": "",
    "atmosphere": "",
    "lighting": "",
    "color_palette": "",
    "mood": "",
    "visual_details": "",
    "style": "{request.style}",
    "negative_prompt": ""
}}

STYLE:

{request.style}

ENVIRONMENT DESCRIPTION:

{request.description}
"""

        result = provider.generate(
            prompt,
            validation_type="environment"
        )

        return EnvironmentEngine._normalize(result)

    # =========================================================
    # MASTER SCRIPT ENVIRONMENT EXTRACTION
    # =========================================================

    @staticmethod
    def extract(request):

        provider = EnvironmentEngine._provider()

        script = (
            request.script
            if request.script
            else ""
        )

        if not script.strip():

            return {
                "success": False,
                "provider": "Ollama",
                "message": "Master Script is empty."
            }

        # -----------------------------------------------------
        # IMPORTANT:
        # This prompt MUST request an ARRAY.
        # -----------------------------------------------------

        prompt = f"""
You are a professional screenplay environment
analyst for MATANGI AI STUDIO.

Your ONLY task is to extract ALL distinct
environments and locations that ACTUALLY EXIST
in the supplied Master Script.

THIS IS AN EXTRACTION TASK.

DO NOT create new environments.

DO NOT creatively rewrite the story.

DO NOT return one environment object.

YOU MUST RETURN AN "environments" ARRAY.

=========================================================
STRICT EXTRACTION RULES
=========================================================

1. Read the complete Master Script.

2. Identify every distinct physical location
   or environment appearing in the screenplay.

3. Extract ONLY locations that actually exist
   in the screenplay.

4. NEVER invent locations.

5. If the same location appears in multiple scenes,
   merge those appearances into ONE environment.

6. Preserve the exact identity of each location.

7. Preserve mythology-specific locations.

8. Do not replace mythology-specific locations
   with generic locations.

9. Do not create locations because they seem
   necessary for the story.

10. Only use information supported by the script.

11. If a particular field is not present,
    return an empty string.

12. The output MUST contain:
    "environments": [...]

13. There can be ONE environment or MANY
    environments.

14. Every environment MUST be an object inside
    the environments array.

15. Return ONLY valid JSON.

=========================================================
REQUIRED OUTPUT FORMAT
=========================================================

{{
    "environments": [
        {{
            "name": "",
            "type": "",
            "description": "",
            "location": "",
            "time_of_day": "",
            "weather": "",
            "terrain": "",
            "architecture": "",
            "materials": "",
            "geography": "",
            "vegetation": "",
            "atmosphere": "",
            "lighting": "",
            "color_palette": "",
            "mood": "",
            "visual_details": "",
            "style": "{request.style}",
            "negative_prompt": ""
        }}
    ]
}}

=========================================================
LANGUAGE
=========================================================

{request.language}

=========================================================
MASTER SCRIPT
=========================================================

{script}
"""

        # -----------------------------------------------------
        # IMPORTANT:
        # Use the normal environment validation because
        # the provider currently maps environment_extraction
        # to the normal environment schema.
        # -----------------------------------------------------

        result = provider.generate(
            prompt,
            validation_type="environment"
        )

        normalized = EnvironmentEngine._normalize(
            result
        )

        if not normalized.get(
            "success",
            False
        ):

            return normalized

        data = normalized.get(
            "data",
            {}
        )

        # =====================================================
        # CASE 1:
        # Correct extraction response
        #
        # {
        #     "environments": [...]
        # }
        # =====================================================

        if isinstance(
            data,
            dict
        ):

            environments = data.get(
                "environments"
            )

            if isinstance(
                environments,
                list
            ):

                return {
                    "success": True,
                    "provider": "Ollama",
                    "data": {
                        "environments":
                            environments
                    }
                }

            # =================================================
            # CASE 2:
            # Ollama returned a SINGLE environment.
            #
            # Convert it into the required list.
            # =================================================

            if (
                data.get("name")
                or data.get("location")
                or data.get("type")
            ):

                return {
                    "success": True,
                    "provider": "Ollama",
                    "data": {
                        "environments": [
                            data
                        ]
                    }
                }

        # =====================================================
        # CASE 3:
        # Direct list
        # =====================================================

        if isinstance(
            data,
            list
        ):

            return {
                "success": True,
                "provider": "Ollama",
                "data": {
                    "environments":
                        data
                }
            }

        # =====================================================
        # FAILED EXTRACTION
        # =====================================================

        return {
            "success": False,
            "provider": "Ollama",
            "message":
                "Ollama returned no valid environments."
        }

    # =========================================================
    # ENVIRONMENT PROFILE
    # =========================================================

    @staticmethod
    def profile(request):

        provider = EnvironmentEngine._provider()

        environment = (
            request.environment
            if request.environment
            else {}
        )

        prompt = f"""
You are a professional cinematic environment
development designer for MATANGI AI STUDIO.

Expand the supplied EXISTING ENVIRONMENT into
a complete production-ready environment profile.

IMPORTANT:

The environment already exists.

DO NOT create a different location.

Preserve:

- Location identity
- Existing architecture
- Existing terrain
- Existing geography
- Existing mythology identity
- Existing story context

Only expand missing visual information where
necessary.

Return ONLY valid JSON.

Use exactly:

{{
    "name": "",
    "type": "",
    "description": "",
    "location": "",
    "time_of_day": "",
    "weather": "",
    "terrain": "",
    "architecture": "",
    "materials": "",
    "geography": "",
    "vegetation": "",
    "atmosphere": "",
    "lighting": "",
    "color_palette": "",
    "mood": "",
    "visual_details": "",
    "style": "{request.style}",
    "negative_prompt": ""
}}

EXISTING ENVIRONMENT:

{json.dumps(
    environment,
    ensure_ascii=False,
    indent=2
)}

MASTER SCRIPT:

{request.master_script}
"""

        result = provider.generate(
            prompt,
            validation_type="environment"
        )

        return EnvironmentEngine._normalize(result)

    # =========================================================
    # ENVIRONMENT CONCEPTS
    # =========================================================

    @staticmethod
    def concepts(request):

        provider = EnvironmentEngine._provider()

        environment = (
            request.environment
            if request.environment
            else {}
        )

        prompt = f"""
You are a professional cinematic environment
concept designer for MATANGI AI STUDIO.

Create exactly FOUR visual concepts for the
EXISTING environment supplied below.

IMPORTANT:

All four concepts MUST represent the SAME
environment/location.

Do NOT change the identity of the location.

Do NOT invent another location.

The concepts may differ in:

- Camera framing
- Composition
- Cinematic viewpoint
- Story presentation
- Atmospheric presentation

CONCEPT TYPES:

Concept 1:
Establishing environment view.

Concept 2:
Detailed environmental presentation.

Concept 3:
Epic cinematic environment presentation.

Concept 4:
Story-appropriate environment presentation.

Return ONLY valid JSON.

Use exactly:

{{
    "environment_name": "",
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

EXISTING ENVIRONMENT:

{json.dumps(
    environment,
    ensure_ascii=False,
    indent=2
)}
"""

        result = provider.generate(
            prompt,
            validation_type="environment_concepts"
        )

        return EnvironmentEngine._normalize(result)

    # =========================================================
    # RESPONSE NORMALIZER
    # =========================================================

    @staticmethod
    def _normalize(result):

        # -----------------------------------------------------
        # INVALID RESULT
        # -----------------------------------------------------

        if not isinstance(
            result,
            dict
        ):

            return {
                "success": False,
                "message":
                    "Invalid response from Ollama."
            }

        # -----------------------------------------------------
        # PROVIDER FAILURE
        # -----------------------------------------------------

        if result.get(
            "success"
        ) is False:

            return result

        # -----------------------------------------------------
        # GET DATA
        # -----------------------------------------------------

        data = result.get(
            "data",
            result.get(
                "output",
                ""
            )
        )

        # -----------------------------------------------------
        # UNWRAP NESTED DATA
        # -----------------------------------------------------

        for _ in range(5):

            if not isinstance(
                data,
                dict
            ):

                break

            if (
                "success" in data
                and data.get(
                    "success"
                ) is False
            ):

                return data

            if (
                "environments" in data
                or "concepts" in data
                or "name" in data
            ):

                break

            if "data" in data:

                next_data = data.get(
                    "data"
                )

                if next_data is data:

                    break

                data = next_data

            else:

                break

        # -----------------------------------------------------
        # DICTIONARY
        # -----------------------------------------------------

        if isinstance(
            data,
            dict
        ):

            return {
                "success": True,
                "data": data
            }

        # -----------------------------------------------------
        # LIST
        # -----------------------------------------------------

        if isinstance(
            data,
            list
        ):

            return {
                "success": True,
                "data": data
            }

        # -----------------------------------------------------
        # EMPTY
        # -----------------------------------------------------

        if data is None:

            return {
                "success": False,
                "message":
                    "Ollama returned an empty response."
            }

        text = str(
            data
        ).strip()

        if not text:

            return {
                "success": False,
                "message":
                    "Ollama returned an empty response."
            }

        # -----------------------------------------------------
        # REMOVE MARKDOWN
        # -----------------------------------------------------

        if text.startswith(
            "```json"
        ):

            text = text[7:]

        elif text.startswith(
            "```"
        ):

            text = text[3:]

        if text.endswith(
            "```"
        ):

            text = text[:-3]

        text = text.strip()

        # -----------------------------------------------------
        # JSON PARSE
        # -----------------------------------------------------

        try:

            parsed = json.loads(
                text
            )

        except json.JSONDecodeError:

            return {
                "success": False,
                "message":
                    "Ollama returned invalid JSON.",
                "raw_data":
                    text
            }

        # -----------------------------------------------------
        # UNWRAP PARSED DATA
        # -----------------------------------------------------

        for _ in range(5):

            if not isinstance(
                parsed,
                dict
            ):

                break

            if (
                "environments" in parsed
                or "concepts" in parsed
                or "name" in parsed
            ):

                break

            if "data" in parsed:

                next_data = parsed.get(
                    "data"
                )

                if next_data is parsed:

                    break

                parsed = next_data

            else:

                break

        # -----------------------------------------------------
        # FINAL RESPONSE
        # -----------------------------------------------------

        return {
            "success": True,
            "data": parsed
        }