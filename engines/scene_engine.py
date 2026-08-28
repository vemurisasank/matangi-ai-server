from core.server_context import server


class SceneEngine:

    @staticmethod
    def generate(request):

        provider = server.provider_manager.get(
            "ollama"
        )

        scene_count = getattr(
            request,
            "scene_count",
            10
        )

        sequence_story = getattr(
            request,
            "sequence_story",
            ""
        )

        movie_description = getattr(
            request,
            "movie_description",
            ""
        )

        style = getattr(
            request,
            "style",
            "Cinematic"
        )

        language = getattr(
            request,
            "language",
            "English"
        )

        characters = getattr(
            request,
            "characters",
            []
        )

        environments = getattr(
            request,
            "environments",
            []
        )

        props = getattr(
            request,
            "props",
            []
        )

        previous_scenes = getattr(
            request,
            "previous_scenes",
            []
        )

        previous_sequence_summaries = getattr(
            request,
            "previous_sequence_summaries",
            []
        )

        continuity_context = getattr(
            request,
            "continuity_context",
            ""
        )

        # -----------------------------------------------------
        # SOURCE STORY
        # -----------------------------------------------------

        source_story = sequence_story.strip()

        if not source_story:

            source_story = getattr(
                request,
                "script",
                ""
            ).strip()

        # -----------------------------------------------------
        # REFERENCE CONTEXT
        # -----------------------------------------------------

        character_context = "\n".join(
            str(character)
            for character in characters
        )

        environment_context = "\n".join(
            str(environment)
            for environment in environments
        )

        prop_context = "\n".join(
            str(prop)
            for prop in props
        )

        # -----------------------------------------------------
        # PREVIOUS SCENE CONTEXT
        # -----------------------------------------------------

        previous_context = "\n".join(
            str(scene)
            for scene in previous_scenes[-10:]
        )

        summary_context = "\n".join(
            str(summary)
            for summary in previous_sequence_summaries[-5:]
        )

        # -----------------------------------------------------
        # SCENE PLANNING PROMPT
        # -----------------------------------------------------

        prompt = f"""
You are an expert feature-film screenplay
scene planner.

Create exactly {scene_count} distinct chronological
scenes from the sequence story below.

============================================================
MOVIE
============================================================

{movie_description}

STYLE:
{style}

LANGUAGE:
{language}

============================================================
SEQUENCE STORY
============================================================

{source_story}

============================================================
AVAILABLE CHARACTERS
============================================================

{character_context}

============================================================
AVAILABLE ENVIRONMENTS
============================================================

{environment_context}

============================================================
AVAILABLE PROPS
============================================================

{prop_context}

============================================================
PREVIOUS SCENES
============================================================

{previous_context}

============================================================
PREVIOUS SEQUENCE SUMMARIES
============================================================

{summary_context}

============================================================
CONTINUITY
============================================================

{continuity_context}

============================================================
MAIN TASK
============================================================

Divide the sequence story into EXACTLY
{scene_count} DIFFERENT scenes.

The scenes must form one continuous
chronological story.

IMPORTANT:

DO NOT copy the complete sequence story
into every scene.

DO NOT repeat scenes.

DO NOT create duplicate story beats.

Each scene must contain a DIFFERENT
part of the story.

Scene 1 starts the sequence.

Scene 2 continues from Scene 1.

Scene 3 continues from Scene 2.

Continue this progression until the
final scene.

The final scene should naturally lead
toward the next sequence.

============================================================
SCENE CONTENT
============================================================

For every scene provide:

1. number
2. title
3. purpose
4. script
5. characters
6. environment
7. props
8. costumes
9. action
10. dialogue
11. image_prompt
12. video_prompt
13. duration

============================================================
LENGTH LIMITS
============================================================

IMPORTANT:

Keep each scene.script under 100 words.

Keep each image_prompt under 40 words.

Keep each video_prompt under 40 words.

Keep dialogue concise.

Do not write long explanations.

Do not repeat information unnecessarily.

============================================================
CONTINUITY
============================================================

Maintain:

- character identity
- character actions
- motivations
- location
- environment
- props
- costumes
- time progression
- emotional progression
- story progression

Characters must not randomly disappear.

Locations must not randomly change
without a story reason.

============================================================
IMAGE PROMPT
============================================================

The image_prompt must describe ONLY
the visual content of that specific scene.

Include the important:

- characters
- action
- environment
- lighting
- composition

Keep it concise.

============================================================
VIDEO PROMPT
============================================================

The video_prompt must describe ONLY
the movement and camera behavior
of that specific scene.

Keep it concise.

============================================================
JSON OUTPUT
============================================================

Return ONLY valid JSON.

Do NOT return markdown.

Do NOT return explanations.

Do NOT return text before or after JSON.

Use exactly this structure:

{{
    "scenes": [
        {{
            "number": 1,
            "title": "Unique scene title",
            "purpose": "Short story purpose",
            "script": "Short individual scene screenplay",
            "characters": [],
            "environment": "Specific environment",
            "props": [],
            "costumes": [],
            "action": "Short specific action",
            "dialogue": "Short dialogue",
            "image_prompt": "Concise visual prompt",
            "video_prompt": "Concise movement and camera prompt",
            "duration": 5
        }}
    ]
}}

The scenes array MUST contain exactly
{scene_count} scenes.

Every scene MUST be different.

Never duplicate the complete sequence story.
"""

        # -----------------------------------------------------
        # GENERATE
        # -----------------------------------------------------

        return provider.generate(
            prompt,
            validation_type="scene",
            num_predict=5000,
            temperature=0.1
        )