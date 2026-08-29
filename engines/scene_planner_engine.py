import json

from core.server_context import server


class ScenePlannerEngine:

    def __init__(self):

        self.provider = server.provider_manager.get(
            "ollama"
        )

    # =========================================================
    # GENERATE SCENES FOR ONE SEQUENCE
    # =========================================================

    def generate_scene_plans(

        self,

        sequence,

        movie_description="",

        master_script="",

        style="Cinematic",

        language="English",

        characters=None,

        environments=None,

        props=None,

        previous_scenes=None,

        previous_sequence_summaries=None,

        continuity_context=""

    ):

        characters = characters or []
        environments = environments or []
        props = props or []
        previous_scenes = previous_scenes or []
        previous_sequence_summaries = (
            previous_sequence_summaries or []
        )

        # =====================================================
        # SEQUENCE DATA
        # =====================================================

        sequence_story = getattr(
            sequence,
            "description",
            ""
        )

        sequence_title = getattr(
            sequence,
            "title",
            ""
        )

        sequence_number = getattr(
            sequence,
            "number",
            0
        )

        act_number = getattr(
            sequence,
            "act_number",
            0
        )

        act_title = getattr(
            sequence,
            "act_title",
            ""
        )

        scene_count = getattr(
            sequence,
            "scene_count",
            1
        )

        starting_scene_number = getattr(
            sequence,
            "starting_scene_number",
            1
        )

        ending_scene_number = getattr(
            sequence,
            "ending_scene_number",
            starting_scene_number + scene_count - 1
        )

        # =====================================================
        # CLEAN CHARACTER INFORMATION
        # =====================================================

        character_context = []

        for character in characters:

            if isinstance(character, dict):

                character_context.append({

                    "name": character.get(
                        "name",
                        ""
                    ),

                    "role": character.get(
                        "role",
                        ""
                    ),

                    "appearance": character.get(
                        "appearance",
                        ""
                    ),

                    "costume": character.get(
                        "costume",
                        ""
                    ),

                    "age": character.get(
                        "age",
                        ""
                    ),

                    "personality": character.get(
                        "personality",
                        ""
                    ),

                    "selected_reference":
                        character.get(
                            "selected_reference",
                            ""
                        ),

                    "reference_images":
                        character.get(
                            "reference_images",
                            []
                        )

                })

            else:

                character_context.append({

                    "name": getattr(
                        character,
                        "name",
                        ""
                    ),

                    "role": getattr(
                        character,
                        "role",
                        ""
                    ),

                    "appearance": getattr(
                        character,
                        "appearance",
                        ""
                    ),

                    "costume": getattr(
                        character,
                        "costume",
                        ""
                    )

                })

        # =====================================================
        # ENVIRONMENT INFORMATION
        # =====================================================

        environment_context = []

        for environment in environments:

            if isinstance(environment, dict):

                environment_context.append({

                    "name": environment.get(
                        "name",
                        ""
                    ),

                    "type": environment.get(
                        "type",
                        ""
                    ),

                    "description": environment.get(
                        "description",
                        ""
                    ),

                    "terrain": environment.get(
                        "terrain",
                        ""
                    ),

                    "lighting": environment.get(
                        "lighting",
                        ""
                    ),

                    "time_of_day":
                        environment.get(
                            "time_of_day",
                            ""
                        ),

                    "reference_images":
                        environment.get(
                            "reference_images",
                            []
                        )

                })

            else:

                environment_context.append({

                    "name": getattr(
                        environment,
                        "name",
                        ""
                    ),

                    "description": getattr(
                        environment,
                        "description",
                        ""
                    )

                })

        # =====================================================
        # PROP INFORMATION
        # =====================================================

        prop_context = []

        for prop in props:

            if isinstance(prop, dict):

                prop_context.append({

                    "name": prop.get(
                        "name",
                        ""
                    ),

                    "description": prop.get(
                        "description",
                        ""
                    )

                })

            else:

                prop_context.append(
                    str(prop)
                )

        # =====================================================
        # MASTER SCRIPT IS MANDATORY FOR REAL EXTRACTION
        # =====================================================

        if not master_script.strip():

            master_script = movie_description

        # =====================================================
        # SCENE PLANNER PROMPT
        # =====================================================

        prompt = f"""
You are the SCENE PLANNER for MATANGI AI STUDIO.

Your job is to convert ONE SEQUENCE from the actual
master screenplay into concrete cinematic production
scenes.

You MUST use the actual story.

Do NOT create generic placeholder scenes.

=========================================================
MASTER SCREENPLAY
=========================================================

{master_script}

=========================================================
CURRENT SEQUENCE
=========================================================

ACT:
{act_number}

ACT TITLE:
{act_title}

SEQUENCE:
{sequence_number}

SEQUENCE TITLE:
{sequence_title}

SEQUENCE STORY:
{sequence_story}

=========================================================
SCENE RANGE
=========================================================

Generate approximately:

{scene_count} scenes.

Global scene range:

{starting_scene_number}
through
{ending_scene_number}

Scene numbers are GLOBAL.

Never restart numbering at 1.

=========================================================
AVAILABLE CHARACTERS
=========================================================

{json.dumps(
    character_context,
    ensure_ascii=False,
    indent=2
)}

=========================================================
AVAILABLE ENVIRONMENTS
=========================================================

{json.dumps(
    environment_context,
    ensure_ascii=False,
    indent=2
)}

=========================================================
AVAILABLE PROPS
=========================================================

{json.dumps(
    prop_context,
    ensure_ascii=False,
    indent=2
)}

=========================================================
PREVIOUS SCENES
=========================================================

{json.dumps(
    previous_scenes,
    ensure_ascii=False,
    indent=2
)}

=========================================================
PREVIOUS SEQUENCE SUMMARIES
=========================================================

{json.dumps(
    previous_sequence_summaries,
    ensure_ascii=False,
    indent=2
)}

=========================================================
CONTINUITY
=========================================================

{continuity_context}

=========================================================
CRITICAL STORY RULE
=========================================================

The master screenplay is the source of truth.

Extract the actual events.

Do NOT replace the story with generic descriptions.

For example, NEVER write:

"The scene opens by establishing the location."

Instead write the actual event from the screenplay.

If the screenplay says:

"Parvati creates Ganesha from the sacred material
and gives him life."

then the scene should describe that actual event.

=========================================================
SCENE DEVELOPMENT
=========================================================

Each scene must represent a meaningful cinematic unit.

A scene should normally contain one or more of:

- a specific story event
- character action
- dialogue
- emotional change
- discovery
- decision
- conflict
- transition
- visual storytelling
- consequence

Do NOT split the sequence into meaningless filler scenes.

Do NOT repeat the same event simply to reach the
requested scene count.

=========================================================
CHARACTER SELECTION
=========================================================

Only include characters actually participating in
the scene.

Do NOT attach every available character to every scene.

For each character used:

characters = [
    "Character Name"
]

character_references should contain only the references
belonging to those characters.

=========================================================
ENVIRONMENT
=========================================================

Select the environment actually used by the scene.

Do not attach every environment.

=========================================================
PROPS
=========================================================

Only include props actually present or used.

=========================================================
COSTUMES
=========================================================

Describe the costume state required for the scene.

Maintain continuity with previous scenes.

=========================================================
DIALOGUE
=========================================================

If dialogue exists in the master screenplay,
preserve its meaning.

Do not invent major dialogue that changes the story.

If the screenplay contains no dialogue for a scene,
use an empty string.

=========================================================
IMAGE PROMPT
=========================================================

Create a production-ready cinematic image prompt
based on the ACTUAL scene.

The prompt must contain:

- characters
- appearance
- costumes
- environment
- action
- emotion
- camera
- composition
- lighting
- cinematic style

Character appearance must remain consistent with
the supplied character references.

=========================================================
VIDEO PROMPT
=========================================================

Create a production-ready video prompt based on the
actual scene.

Describe:

- character movement
- physical action
- camera movement
- environment movement
- emotional performance
- continuity

Do not describe a static image.

=========================================================
DURATION
=========================================================

Use a realistic duration for the scene.

Short visual beat:
3-5 seconds

Normal scene:
5-10 seconds

Dialogue/action scene:
8-15 seconds

Do not automatically set every scene to 5 seconds.

=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON.

Use exactly:

{{
    "scenes": [
        {{
            "number": {starting_scene_number},
            "act_number": {act_number},
            "act_title": "{act_title}",
            "sequence_number": {sequence_number},
            "sequence_title": "{sequence_title}",

            "title": "",
            "purpose": "",

            "script": "",

            "characters": [],
            "character_references": [],

            "environment": "",
            "environment_references": [],

            "props": [],
            "costumes": [],

            "action": "",
            "dialogue": "",

            "image_prompt": "",
            "video_prompt": "",

            "duration": 5,

            "previous_scene_number": 0,
            "next_scene_number": 0,

            "continuity_notes": "",

            "status": "Planned"
        }}
    ]
}}

IMPORTANT:

Generate the requested scene range.

Every scene must be based on actual screenplay
content.

Return ONLY JSON.
"""

        # =====================================================
        # CALL OLLAMA
        # =====================================================

        try:

            result = self.provider.generate(

                prompt,

                validate_prompt=False,

                num_predict=12000,

                temperature=0.2

            )

            if not result.get("success"):

                return result

            raw_output = result.get(
                "output",
                ""
            )

            # =================================================
            # PARSE JSON
            # =================================================

            try:

                parsed = json.loads(
                    raw_output
                )

            except json.JSONDecodeError:

                # Attempt extraction of JSON object
                start = raw_output.find("{")
                end = raw_output.rfind("}")

                if start == -1 or end == -1:

                    return {
                        "success": False,
                        "provider": "Ollama",
                        "message":
                            "Scene planner returned invalid JSON.",
                        "output":
                            raw_output
                    }

                try:

                    parsed = json.loads(
                        raw_output[
                            start:end + 1
                        ]
                    )

                except Exception as error:

                    return {
                        "success": False,
                        "provider": "Ollama",
                        "message":
                            f"Unable to parse scene JSON: {error}",
                        "output":
                            raw_output
                    }

            # =================================================
            # NORMALIZE
            # =================================================

            scenes = parsed.get(
                "scenes",
                []
            )

            if not isinstance(
                scenes,
                list
            ):

                return {
                    "success": False,
                    "provider": "Ollama",
                    "message":
                        "Invalid scenes array.",
                    "output":
                        parsed
                }

            # =================================================
            # FIX GLOBAL NUMBERING
            # =================================================

            for index, scene in enumerate(
                scenes
            ):

                expected_number = (
                    starting_scene_number
                    + index
                )

                scene["number"] = (
                    expected_number
                )

                scene[
                    "act_number"
                ] = act_number

                scene[
                    "act_title"
                ] = act_title

                scene[
                    "sequence_number"
                ] = sequence_number

                scene[
                    "sequence_title"
                ] = sequence_title

                scene[
                    "previous_scene_number"
                ] = (
                    expected_number - 1
                    if expected_number > 1
                    else 0
                )

                scene[
                    "next_scene_number"
                ] = (
                    expected_number + 1
                )

                scene.setdefault(
                    "status",
                    "Planned"
                )

            return {

                "success": True,

                "provider": "Ollama",

                "data": {

                    "scenes": scenes

                }

            }

        except Exception as error:

            return {

                "success": False,

                "provider": "Ollama",

                "message": str(error)

            }