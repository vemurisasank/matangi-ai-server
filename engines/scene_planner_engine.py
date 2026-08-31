import json
import re

from core.server_context import server


# =============================================================
# MATANGI AI STUDIO
# SCENE PLANNER ENGINE
# =============================================================
#
# PIPELINE
#
# Master Script
#      ↓
# Movie Structure
#      ↓
# Act
#      ↓
# Sequence
#      ↓
# Scene Planner
#      ↓
# Scene Plans
#      ↓
# Scene Reference Package
#      ↓
# Image Generation
#
# IMPORTANT
#
# The Scene Planner does NOT own references.
#
# Studio supplies:
#
#   Characters
#   Environments
#   Props
#   References
#
# Ollama supplies:
#
#   Story beat
#   Scene description
#   Action
#   Dialogue
#   Image prompt
#   Video prompt
#
# The SERVER is authoritative for:
#
#   scene numbering
#   character whitelist
#   environment whitelist
#   prop whitelist
#   references
#   costumes from character data
#
# =============================================================


class ScenePlannerEngine:

    def __init__(self):

        self.provider_name = "Ollama"

    # =========================================================
    # PUBLIC API
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

        # -----------------------------------------------------
        # NORMALIZE SOURCE DATA
        # -----------------------------------------------------

        sequence_data = self._to_dict(
            sequence
        )

        character_data = (
            self._normalize_characters(
                characters
            )
        )

        environment_data = (
            self._normalize_environments(
                environments
            )
        )

        prop_data = (
            self._normalize_props(
                props
            )
        )

        previous_scene_data = (
            self._normalize_previous_scenes(
                previous_scenes
            )
        )

        previous_summary_data = (
            self._normalize_previous_sequence_summaries(
                previous_sequence_summaries
            )
        )

        # -----------------------------------------------------
        # SCENE COUNT
        # -----------------------------------------------------

        scene_count = self._safe_int(
            sequence_data.get(
                "scene_count",
                1
            ),
            1
        )

        scene_count = max(
            1,
            scene_count
        )

        # -----------------------------------------------------
        # GLOBAL STARTING NUMBER
        # -----------------------------------------------------

        starting_scene = self._safe_int(
            sequence_data.get(
                "starting_scene_number",
                1
            ),
            1
        )

        starting_scene = max(
            1,
            starting_scene
        )

        ending_scene = (
            starting_scene
            + scene_count
            - 1
        )

        sequence_data[
            "scene_count"
        ] = scene_count

        sequence_data[
            "starting_scene_number"
        ] = starting_scene

        sequence_data[
            "ending_scene_number"
        ] = ending_scene

        # -----------------------------------------------------
        # BUILD PROMPT
        # -----------------------------------------------------

        prompt = self._build_prompt(
            sequence=sequence_data,
            movie_description=movie_description,
            master_script=master_script,
            style=style,
            language=language,
            characters=character_data,
            environments=environment_data,
            props=prop_data,
            previous_scenes=previous_scene_data,
            previous_sequence_summaries=(
                previous_summary_data
            ),
            continuity_context=continuity_context
        )

        # -----------------------------------------------------
        # OLLAMA PROVIDER
        # -----------------------------------------------------

        try:

            provider = (
                server
                .provider_manager
                .get(
                    "ollama"
                )
            )

        except Exception as error:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": (
                    "Unable to access Ollama provider: "
                    f"{error}"
                )
            }

        if provider is None:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": (
                    "Ollama provider is not configured "
                    "in Matangi Server."
                )
            }

        # -----------------------------------------------------
        # GENERATE
        # -----------------------------------------------------

        try:

            result = provider.generate(
                prompt,
                validation_type="scene",
                num_predict=7000,
                temperature=0.1
            )

        except TypeError:

            try:

                result = provider.generate(
                    prompt
                )

            except Exception as error:

                return {
                    "success": False,
                    "provider": self.provider_name,
                    "message": (
                        "Scene planning failed: "
                        f"{error}"
                    )
                }

        except Exception as error:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": (
                    "Scene planning failed: "
                    f"{error}"
                )
            }

        # -----------------------------------------------------
        # PROVIDER RESPONSE
        # -----------------------------------------------------

        if not isinstance(
            result,
            dict
        ):

            return {
                "success": False,
                "provider": self.provider_name,
                "message": (
                    "Ollama returned an invalid "
                    "response."
                ),
                "raw_data": result
            }

        if not result.get(
            "success",
            False
        ):

            return result

        raw_data = (
            result.get("output")
            or result.get("data")
            or result.get("response")
            or result.get("text")
        )

        if raw_data is None:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": (
                    "Ollama returned no scene "
                    "generation output."
                ),
                "raw_data": result
            }

        # -----------------------------------------------------
        # PARSE
        # -----------------------------------------------------

        try:

            parsed = self._parse_json(
                raw_data
            )

        except Exception as error:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": (
                    "Unable to parse scene planner "
                    f"JSON: {error}"
                ),
                "raw_data": raw_data
            }

        # -----------------------------------------------------
        # EXTRACT SCENES
        # -----------------------------------------------------

        scenes = self._extract_scene_list(
            parsed
        )

        if not scenes:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": (
                    "Scene planner returned no scenes."
                ),
                "raw_data": parsed
            }

        # -----------------------------------------------------
        # NORMALIZE
        # -----------------------------------------------------

        normalized_scenes = (
            self._normalize_scene_list(
                scenes=scenes,
                sequence=sequence_data,
                characters=character_data,
                environments=environment_data,
                props=prop_data,
                starting_scene=starting_scene,
                expected_count=scene_count
            )
        )

        # -----------------------------------------------------
        # EXACT SCENE COUNT
        # -----------------------------------------------------

        if len(normalized_scenes) != scene_count:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": (
                    "Scene planner returned "
                    f"{len(normalized_scenes)} scenes, "
                    f"but exactly {scene_count} scenes "
                    "were requested."
                ),
                "expected_scene_count": scene_count,
                "actual_scene_count": len(
                    normalized_scenes
                ),
                "raw_data": parsed
            }

        # -----------------------------------------------------
        # VALIDATE SUPPLIED ENTITIES
        # -----------------------------------------------------

        entity_validation = (
            self._validate_scene_entities(
                normalized_scenes,
                character_data,
                environment_data,
                prop_data
            )
        )

        if not entity_validation["success"]:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": entity_validation[
                    "message"
                ],
                "raw_data": normalized_scenes
            }

        # -----------------------------------------------------
        # GLOBAL NUMBERING
        # -----------------------------------------------------

        self._finalize_scene_numbers(
            normalized_scenes,
            starting_scene
        )

        # -----------------------------------------------------
        # SERVER-CONTROLLED COSTUMES
        # -----------------------------------------------------

        self._finalize_costumes(
            normalized_scenes,
            character_data
        )

        # -----------------------------------------------------
        # SERVER-CONTROLLED REFERENCES
        # -----------------------------------------------------

        self._finalize_references(
            normalized_scenes,
            character_data,
            environment_data,
            prop_data
        )

        # -----------------------------------------------------
        # FINAL PROMPT VALIDATION
        # -----------------------------------------------------

        prompt_validation = (
            self._validate_scene_prompts(
                normalized_scenes
            )
        )

        if not prompt_validation["success"]:

            return {
                "success": False,
                "provider": self.provider_name,
                "message": prompt_validation[
                    "message"
                ],
                "raw_data": normalized_scenes
            }

        # -----------------------------------------------------
        # FINAL OUTPUT
        # -----------------------------------------------------

        return {
            "success": True,
            "provider": self.provider_name,
            "data": normalized_scenes
        }

    # =========================================================
    # PROMPT BUILDER
    # =========================================================

    def _build_prompt(
        self,
        sequence,
        movie_description,
        master_script,
        style,
        language,
        characters,
        environments,
        props,
        previous_scenes,
        previous_sequence_summaries,
        continuity_context
    ):

        sequence_number = self._safe_int(
            sequence.get(
                "number",
                1
            ),
            1
        )

        act_number = self._safe_int(
            sequence.get(
                "act_number",
                1
            ),
            1
        )

        act_title = str(
            sequence.get(
                "act_title",
                ""
            )
            or ""
        )

        sequence_title = str(
            sequence.get(
                "title",
                ""
            )
            or ""
        )

        sequence_description = str(
            sequence.get(
                "description",
                ""
            )
            or ""
        )

        sequence_purpose = str(
            sequence.get(
                "purpose",
                ""
            )
            or ""
        )

        sequence_location = str(
            sequence.get(
                "location",
                ""
            )
            or ""
        )

        sequence_characters = (
            sequence.get(
                "characters",
                []
            )
            or []
        )

        important_events = (
            sequence.get(
                "important_events",
                []
            )
            or []
        )

        emotional_progression = str(
            sequence.get(
                "emotional_progression",
                ""
            )
            or ""
        )

        visual_opportunities = (
            sequence.get(
                "visual_opportunities",
                []
            )
            or []
        )

        sequence_continuity = str(
            sequence.get(
                "continuity_notes",
                ""
            )
            or ""
        )

        scene_count = self._safe_int(
            sequence.get(
                "scene_count",
                1
            ),
            1
        )

        starting_scene = self._safe_int(
            sequence.get(
                "starting_scene_number",
                1
            ),
            1
        )

        ending_scene = self._safe_int(
            sequence.get(
                "ending_scene_number",
                starting_scene + scene_count - 1
            ),
            starting_scene + scene_count - 1
        )

        # -----------------------------------------------------
        # CONTEXT
        # -----------------------------------------------------

        character_context = self._json_text(
            characters
        )

        environment_context = self._json_text(
            environments
        )

        prop_context = self._json_text(
            props
        )

        previous_scene_context = self._json_text(
            previous_scenes[-10:]
        )

        previous_summary_context = self._json_text(
            previous_sequence_summaries[-5:]
        )

        sequence_characters_context = (
            self._json_text(
                sequence_characters
            )
        )

        important_events_context = (
            self._json_text(
                important_events
            )
        )

        visual_opportunities_context = (
            self._json_text(
                visual_opportunities
            )
        )

        master_script_context = (
            master_script.strip()
            if master_script
            else ""
        )

        # -----------------------------------------------------
        # PROMPT
        # -----------------------------------------------------

        return f"""
You are the FEATURE FILM SCENE PLANNER
for MATANGI AI STUDIO.

Your job is to transform ONE EXISTING
STORY SEQUENCE into individual production scenes.

You are NOT writing a new movie.

You are NOT rewriting the supplied story.

You are NOT inventing mythology.

You are NOT inventing characters.

You are NOT inventing locations.

============================================================
MOVIE
============================================================

Movie Description:

{movie_description}

Visual Style:

{style}

Language:

{language}

============================================================
MASTER SCRIPT
============================================================

The master script is the highest-level
source of truth.

MASTER SCRIPT:

{master_script_context}

============================================================
CURRENT ACT
============================================================

Act Number:

{act_number}

Act Title:

{act_title}

============================================================
CURRENT SEQUENCE
============================================================

Sequence Number:

{sequence_number}

Sequence Title:

{sequence_title}

Sequence Description:

{sequence_description}

Sequence Purpose:

{sequence_purpose}

Sequence Location:

{sequence_location}

Sequence Characters:

{sequence_characters_context}

Important Events:

{important_events_context}

Emotional Progression:

{emotional_progression}

Visual Opportunities:

{visual_opportunities_context}

Sequence Continuity:

{sequence_continuity}

============================================================
SCENE COUNT
============================================================

You MUST generate EXACTLY:

{scene_count}

scenes.

Global range:

{starting_scene}

through

{ending_scene}

Do not generate fewer scenes.

Do not generate more scenes.

============================================================
CHARACTER WHITELIST
============================================================

You may use ONLY characters contained in this
supplied list:

{character_context}

IMPORTANT:

Every character is a separate identity.

If the supplied list contains:

Human form Ganesha

and:

Bala Ganesha (Pre-Transformation)

they are DIFFERENT character records.

Do NOT merge them.

Do NOT rename them.

Do NOT convert one into another.

Do NOT replace a supplied character with
a generic version.

Use the exact supplied name.

============================================================
ENVIRONMENT WHITELIST
============================================================

You may use ONLY environments contained in:

{environment_context}

Do not invent locations.

Do not rename locations.

Do not create alternate environment identities.

============================================================
PROP WHITELIST
============================================================

You may use ONLY props contained in:

{prop_context}

Do not invent important props.

============================================================
REFERENCE RULE
============================================================

REFERENCES ARE OPTIONAL.

The Studio already supplies actual reference
information.

Do NOT invent reference paths.

NEVER create:

reference_images/Parvati

reference_images/Ganesha

reference_images/Shiva

reference_images/Mount Kailash

or any other artificial reference path.

The server will attach actual references after
scene generation.

If no reference exists or was not selected,
the final reference list MUST remain empty.

============================================================
COSTUME RULE
============================================================

Costumes should come from the supplied
character information whenever possible.

Do NOT invent generic costumes such as:

"Divine Mother costume"

"Divine Guardian costume"

"Supreme Deity costume"

unless that exact costume information exists
in the supplied character record.

If the selected character has costume information,
use that information.

If no costume information exists:

return an empty costumes list.

============================================================
SCENE DEVELOPMENT
============================================================

Create exactly {scene_count} scenes.

Every scene must represent ONE DISTINCT
CHRONOLOGICAL STORY BEAT.

This is extremely important.

DO NOT combine multiple major story beats
into one scene.

For example, do NOT make one scene contain:

Parvati creates Ganesha,
Ganesha comes alive,
Parvati gives instructions,
and Shiva arrives.

Those are separate developments.

Instead:

Scene A:
Parvati creates Ganesha.

Scene B:
Ganesha comes alive.

Scene C:
Parvati instructs Ganesha.

Scene D:
Shiva approaches.

Each scene must have one primary dramatic
purpose.

============================================================
CHRONOLOGICAL PROGRESSION
============================================================

Scene 1 begins the sequence.

Scene 2 happens after Scene 1.

Scene 3 happens after Scene 2.

Continue in chronological order.

Every scene must follow naturally from the
previous scene.

Do not jump backward unless the supplied
story explicitly requires a flashback.

Do not skip important supplied events.

Do not repeat an already completed event.

============================================================
NO ARTIFICIAL PADDING
============================================================

Do NOT create meaningless scenes such as:

"Camera looks at mountain."

"Character looks around."

"Wide shot of location."

unless that visual beat actually advances
the supplied story.

Every scene must contain meaningful story
development.

============================================================
CHARACTER RULES
============================================================

Use only characters from the supplied
character whitelist.

The character names in the final JSON must
match the supplied names.

Do not invent:

- gods
- humans
- guards
- soldiers
- servants
- animals
- crowds
- background characters

unless they are explicitly supplied or required
by the source story.

============================================================
ENVIRONMENT RULES
============================================================

Use only supplied environments.

If the sequence stays in the same environment,
maintain that environment.

Do not randomly move the story.

============================================================
SCENE SCRIPT
============================================================

Each scene script should describe ONLY the
individual event occurring in that scene.

Keep it concise.

Normally under approximately 100 words.

============================================================
ACTION
============================================================

Action must describe the primary action of
THIS scene.

Do not combine unrelated major events.

============================================================
DIALOGUE
============================================================

Use dialogue only when appropriate.

Dialogue should be based on the supplied
story and character situation.

Do not add unnecessary dialogue.

If no dialogue is required:

""

============================================================
IMAGE PROMPT
============================================================

The image prompt is for the image-generation
pipeline.

It must describe the exact visual state
of THIS scene.

Include only relevant:

- characters
- character appearance
- action
- environment
- composition
- lighting
- mood
- important supplied props
- cinematic framing

The image prompt must NOT describe a different
scene.

It must NOT summarize the entire sequence.

It must be useful to an image-generation model.

============================================================
VIDEO PROMPT
============================================================

The video prompt is for video generation.

Describe ONLY movement belonging to THIS scene.

Include:

- character movement
- physical action
- camera movement
- environmental motion
- cinematic motion

Do not describe future events.

Do not describe another scene.

============================================================
CONTINUITY
============================================================

Maintain:

- character identity
- character form
- character appearance
- character costume
- environment
- props
- chronology
- emotional progression
- cause and effect

Special character forms supplied by Studio
must remain intact.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

No Markdown.

No code fences.

No explanation.

No text before JSON.

No text after JSON.

Use:

{{
    "scenes": [
        {{
            "number": {starting_scene},
            "title": "",
            "purpose": "",
            "script": "",
            "characters": [],
            "character_references": [],
            "environment": "",
            "environment_references": [],
            "props": [],
            "prop_references": [],
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

============================================================
FINAL SELF-CHECK
============================================================

Before returning JSON verify:

1. Exactly {scene_count} scenes.

2. Each scene is one distinct story beat.

3. No scene combines multiple major events.

4. Scenes are chronological.

5. No duplicated story beat.

6. Characters exist in supplied character list.

7. Character names are exact.

8. Human form Ganesha and Bala Ganesha
   (Pre-Transformation) remain separate if
   supplied separately.

9. Environments exist in supplied list.

10. Props exist in supplied list.

11. No invented reference paths.

12. No fake reference_images paths.

13. Costume values come from character data
    when available.

14. Empty reference selections stay empty.

15. Image prompt describes THIS scene.

16. Video prompt describes THIS scene.

17. JSON is valid.

Return ONLY JSON.
"""

    # =========================================================
    # VALIDATE SUPPLIED ENTITIES
    # =========================================================

    def _validate_scene_entities(
        self,
        scenes,
        characters,
        environments,
        props
    ):

        character_names = {
            self._normalize_name(
                self._extract_name(
                    item
                )
            )
            for item in characters
            if self._extract_name(item)
        }

        environment_names = {
            self._normalize_name(
                self._extract_name(
                    item
                )
            )
            for item in environments
            if self._extract_name(item)
        }

        prop_names = {
            self._normalize_name(
                self._extract_name(
                    item
                )
            )
            for item in props
            if self._extract_name(item)
        }

        # -----------------------------------------------------
        # Character validation
        # -----------------------------------------------------

        for scene in scenes:

            for name in scene.get(
                "characters",
                []
            ):

                normalized = self._normalize_name(
                    name
                )

                if normalized not in character_names:

                    return {
                        "success": False,
                        "message": (
                            "Scene "
                            f"{scene.get('number')} "
                            "contains character "
                            f"'{name}' which is not "
                            "in the supplied character list."
                        )
                    }

        # -----------------------------------------------------
        # Environment validation
        # -----------------------------------------------------

        for scene in scenes:

            environment = self._normalize_name(
                scene.get(
                    "environment",
                    ""
                )
            )

            if (
                environment
                and environment_names
                and environment not in environment_names
            ):

                return {
                    "success": False,
                    "message": (
                        "Scene "
                        f"{scene.get('number')} "
                        "contains environment "
                        f"'{scene.get('environment')}' "
                        "which is not in the supplied "
                        "environment list."
                    )
                }

        # -----------------------------------------------------
        # Prop validation
        # -----------------------------------------------------

        for scene in scenes:

            for prop in scene.get(
                "props",
                []
            ):

                normalized = self._normalize_name(
                    prop
                )

                if (
                    prop_names
                    and normalized not in prop_names
                ):

                    return {
                        "success": False,
                        "message": (
                            "Scene "
                            f"{scene.get('number')} "
                            "contains prop "
                            f"'{prop}' which is not "
                            "in the supplied prop list."
                        )
                    }

        return {
            "success": True
        }

    # =========================================================
    # VALIDATE PROMPTS
    # =========================================================

    def _validate_scene_prompts(
        self,
        scenes
    ):

        for scene in scenes:

            number = scene.get(
                "number"
            )

            image_prompt = str(
                scene.get(
                    "image_prompt",
                    ""
                )
                or ""
            ).strip()

            video_prompt = str(
                scene.get(
                    "video_prompt",
                    ""
                )
                or ""
            ).strip()

            if not image_prompt:

                return {
                    "success": False,
                    "message": (
                        f"Scene {number} has an empty "
                        "image_prompt."
                    )
                }

            if not video_prompt:

                return {
                    "success": False,
                    "message": (
                        f"Scene {number} has an empty "
                        "video_prompt."
                    )
                }

        return {
            "success": True
        }

    # =========================================================
    # FINALIZE GLOBAL NUMBERS
    # =========================================================

    @staticmethod
    def _finalize_scene_numbers(
        scenes,
        starting_scene
    ):

        total = len(
            scenes
        )

        for index, scene in enumerate(
            scenes
        ):

            number = (
                starting_scene
                + index
            )

            scene["number"] = number

            scene["previous_scene_number"] = (
                number - 1
                if index > 0
                else 0
            )

            scene["next_scene_number"] = (
                number + 1
                if index < total - 1
                else 0
            )

            scene["status"] = (
                scene.get(
                    "status",
                    "Planned"
                )
                or "Planned"
            )

    # =========================================================
    # FINALIZE COSTUMES
    # =========================================================

    def _finalize_costumes(
        self,
        scenes,
        characters
    ):

        character_map = (
            self._build_name_map(
                characters
            )
        )

        for scene in scenes:

            final_costumes = []

            scene_characters = (
                scene.get(
                    "characters",
                    []
                )
            )

            for character_name in scene_characters:

                character = self._find_by_name(
                    character_map,
                    character_name
                )

                if character is None:
                    continue

                costume_values = (
                    self._extract_costume_data(
                        character
                    )
                )

                final_costumes.extend(
                    costume_values
                )

            # -------------------------------------------------
            # Only use AI costumes if no character costume
            # information exists.
            #
            # Even then, we reject obvious generic invented
            # costume labels.
            # -------------------------------------------------

            if not final_costumes:

                ai_costumes = self._clean_name_list(
                    scene.get(
                        "costumes",
                        []
                    )
                )

                for costume in ai_costumes:

                    if self._is_generic_invented_costume(
                        costume
                    ):

                        continue

                    final_costumes.append(
                        costume
                    )

            scene["costumes"] = (
                self._deduplicate(
                    final_costumes
                )
            )

    # =========================================================
    # EXTRACT COSTUME DATA
    # =========================================================

    def _extract_costume_data(
        self,
        item
    ):

        if not isinstance(
            item,
            dict
        ):

            return []

        result = []

        # -----------------------------------------------------
        # Common direct costume fields
        # -----------------------------------------------------

        direct_keys = (
            "costume",
            "outfit",
            "attire",
            "clothing",
            "dress",
            "wardrobe"
        )

        for key in direct_keys:

            value = item.get(
                key
            )

            if isinstance(
                value,
                str
            ):

                if value.strip():

                    result.append(
                        value.strip()
                    )

            elif isinstance(
                value,
                list
            ):

                result.extend(
                    self._clean_name_list(
                        value
                    )
                )

            elif isinstance(
                value,
                dict
            ):

                name = self._extract_name(
                    value
                )

                if name:

                    result.append(
                        name
                    )

        # -----------------------------------------------------
        # Common list fields
        # -----------------------------------------------------

        for key in (
            "costumes",
            "outfits",
            "attires",
            "wardrobes"
        ):

            value = item.get(
                key
            )

            if isinstance(
                value,
                str
            ):

                if value.strip():

                    result.append(
                        value.strip()
                    )

            elif isinstance(
                value,
                list
            ):

                result.extend(
                    self._clean_name_list(
                        value
                    )
                )

        return self._deduplicate(
            result
        )

    # =========================================================
    # GENERIC COSTUME FILTER
    # =========================================================

    @staticmethod
    def _is_generic_invented_costume(
        costume
    ):

        text = str(
            costume
        ).strip().lower()

        generic_values = {
            "divine mother costume",
            "divine guardian costume",
            "supreme deity costume",
            "divine costume",
            "mythological costume",
            "traditional costume",
            "hero costume",
            "villain costume",
            "god costume",
            "goddess costume"
        }

        return text in generic_values

    # =========================================================
    # FINALIZE REFERENCES
    # =========================================================

    def _finalize_references(
        self,
        scenes,
        characters,
        environments,
        props
    ):

        character_map = (
            self._build_name_map(
                characters
            )
        )

        environment_map = (
            self._build_name_map(
                environments
            )
        )

        prop_map = (
            self._build_name_map(
                props
            )
        )

        for scene in scenes:

            # -------------------------------------------------
            # CHARACTER REFERENCES
            # -------------------------------------------------

            final_character_refs = []

            for character_name in (
                self._clean_name_list(
                    scene.get(
                        "characters",
                        []
                    )
                )
            ):

                supplied_character = (
                    self._find_by_name(
                        character_map,
                        character_name
                    )
                )

                if supplied_character is None:
                    continue

                final_character_refs.extend(
                    self._extract_reference_data(
                        supplied_character
                    )
                )

            # -------------------------------------------------
            # ENVIRONMENT REFERENCES
            # -------------------------------------------------

            final_environment_refs = []

            environment_name = str(
                scene.get(
                    "environment",
                    ""
                )
                or ""
            ).strip()

            if environment_name:

                supplied_environment = (
                    self._find_by_name(
                        environment_map,
                        environment_name
                    )
                )

                if supplied_environment is not None:

                    final_environment_refs.extend(
                        self._extract_reference_data(
                            supplied_environment
                        )
                    )

            # -------------------------------------------------
            # PROP REFERENCES
            # -------------------------------------------------

            final_prop_refs = []

            for prop_name in (
                self._clean_name_list(
                    scene.get(
                        "props",
                        []
                    )
                )
            ):

                supplied_prop = (
                    self._find_by_name(
                        prop_map,
                        prop_name
                    )
                )

                if supplied_prop is None:
                    continue

                final_prop_refs.extend(
                    self._extract_reference_data(
                        supplied_prop
                    )
                )

            # -------------------------------------------------
            # FINAL REFERENCE ARRAYS
            # -------------------------------------------------

            scene[
                "character_references"
            ] = self._deduplicate(
                final_character_refs
            )

            scene[
                "environment_references"
            ] = self._deduplicate(
                final_environment_refs
            )

            scene[
                "prop_references"
            ] = self._deduplicate(
                final_prop_refs
            )

    # =========================================================
    # BUILD NAME MAP
    # =========================================================

    def _build_name_map(
        self,
        items
    ):

        result = {}

        for item in items:

            normalized = self._to_dict(
                item
            )

            name = self._extract_name(
                normalized
            )

            if not name:
                continue

            result[
                self._normalize_name(
                    name
                )
            ] = normalized

        return result

    # =========================================================
    # FIND BY NAME
    # =========================================================

    @staticmethod
    def _find_by_name(
        mapping,
        name
    ):

        return mapping.get(
            ScenePlannerEngine._normalize_name(
                name
            )
        )

    # =========================================================
    # EXTRACT NAME
    # =========================================================

    @staticmethod
    def _extract_name(
        value
    ):

        if isinstance(
            value,
            str
        ):

            return value.strip()

        if isinstance(
            value,
            dict
        ):

            for key in (
                "name",
                "character_name",
                "environment_name",
                "prop_name",
                "title"
            ):

                if value.get(
                    key
                ):

                    return str(
                        value.get(
                            key
                        )
                    ).strip()

        return ""

    # =========================================================
    # EXTRACT REAL REFERENCES
    # =========================================================

    def _extract_reference_data(
        self,
        item
    ):

        if not isinstance(
            item,
            dict
        ):

            return []

        result = []

        # -----------------------------------------------------
        # Direct reference fields
        # -----------------------------------------------------

        direct_keys = (
            "selected_reference",
            "selected_reference_path",
            "reference",
            "reference_path",
            "reference_image",
            "reference_image_path",
            "master_reference",
            "master_reference_path",
            "image_path",
            "file_path",
            "asset_path",
            "path",
            "file"
        )

        for key in direct_keys:

            value = item.get(
                key
            )

            if isinstance(
                value,
                str
            ) and value.strip():

                result.append(
                    value.strip()
                )

        # -----------------------------------------------------
        # Reference lists
        # -----------------------------------------------------

        list_keys = (
            "reference_images",
            "references",
            "reference_paths",
            "selected_references",
            "master_references"
        )

        for key in list_keys:

            values = item.get(
                key,
                []
            )

            if isinstance(
                values,
                str
            ):

                if values.strip():

                    result.append(
                        values.strip()
                    )

            elif isinstance(
                values,
                (list, tuple)
            ):

                for value in values:

                    if isinstance(
                        value,
                        str
                    ) and value.strip():

                        result.append(
                            value.strip()
                        )

                    elif isinstance(
                        value,
                        dict
                    ):

                        result.extend(
                            self._extract_reference_data(
                                value
                            )
                        )

        # -----------------------------------------------------
        # Reference objects
        # -----------------------------------------------------

        reference_data = item.get(
            "reference_data",
            []
        )

        if isinstance(
            reference_data,
            dict
        ):

            reference_data = [
                reference_data
            ]

        if isinstance(
            reference_data,
            (list, tuple)
        ):

            for reference in reference_data:

                if isinstance(
                    reference,
                    str
                ):

                    if reference.strip():

                        result.append(
                            reference.strip()
                        )

                elif isinstance(
                    reference,
                    dict
                ):

                    result.extend(
                        self._extract_reference_data(
                            reference
                        )
                    )

        # -----------------------------------------------------
        # Nested reference structures
        # -----------------------------------------------------

        for key in (
            "asset",
            "master_reference_data",
            "selected_reference_data"
        ):

            nested = item.get(
                key
            )

            if isinstance(
                nested,
                dict
            ):

                result.extend(
                    self._extract_reference_data(
                        nested
                    )
                )

        # -----------------------------------------------------
        # IMPORTANT
        #
        # ONLY supplied reference values are returned.
        #
        # No reference_images/Name creation.
        # -----------------------------------------------------

        return [
            value
            for value in self._deduplicate(
                result
            )
            if isinstance(
                value,
                str
            )
            and value.strip()
        ]

    # =========================================================
    # NORMALIZE CHARACTERS
    # =========================================================

    def _normalize_characters(
        self,
        characters
    ):

        result = []

        for character in characters:

            normalized = self._normalize_item(
                character
            )

            if normalized is not None:

                result.append(
                    normalized
                )

        return result

    # =========================================================
    # NORMALIZE ENVIRONMENTS
    # =========================================================

    def _normalize_environments(
        self,
        environments
    ):

        result = []

        for environment in environments:

            normalized = self._normalize_item(
                environment
            )

            if normalized is not None:

                result.append(
                    normalized
                )

        return result

    # =========================================================
    # NORMALIZE PROPS
    # =========================================================

    def _normalize_props(
        self,
        props
    ):

        result = []

        for prop in props:

            normalized = self._normalize_item(
                prop
            )

            if normalized is not None:

                result.append(
                    normalized
                )

        return result

    # =========================================================
    # NORMALIZE PREVIOUS SCENES
    # =========================================================

    def _normalize_previous_scenes(
        self,
        scenes
    ):

        result = []

        for scene in scenes:

            normalized = self._normalize_item(
                scene
            )

            if normalized is not None:

                result.append(
                    normalized
                )

        return result

    # =========================================================
    # NORMALIZE PREVIOUS SUMMARIES
    # =========================================================

    def _normalize_previous_sequence_summaries(
        self,
        summaries
    ):

        result = []

        for summary in summaries:

            normalized = self._normalize_item(
                summary
            )

            if normalized is not None:

                result.append(
                    normalized
                )

        return result

    # =========================================================
    # NORMALIZE ITEM
    # =========================================================

    def _normalize_item(
        self,
        item
    ):

        if item is None:

            return None

        if isinstance(
            item,
            str
        ):

            return item

        if isinstance(
            item,
            dict
        ):

            return {
                key: value
                for key, value in item.items()
                if value not in (
                    None,
                    ""
                )
            }

        try:

            return {
                key: value
                for key, value in vars(item).items()
                if value not in (
                    None,
                    ""
                )
            }

        except Exception:

            pass

        result = {}

        for key in dir(item):

            if key.startswith("_"):
                continue

            try:

                value = getattr(
                    item,
                    key
                )

            except Exception:

                continue

            if callable(value):
                continue

            if value in (
                None,
                ""
            ):
                continue

            result[key] = value

        return result

    # =========================================================
    # EXTRACT SCENE LIST
    # =========================================================

    def _extract_scene_list(
        self,
        data
    ):

        if isinstance(
            data,
            list
        ):

            return data

        if not isinstance(
            data,
            dict
        ):

            return []

        scenes = data.get(
            "scenes"
        )

        if isinstance(
            scenes,
            list
        ):

            return scenes

        nested = data.get(
            "data"
        )

        if isinstance(
            nested,
            dict
        ):

            scenes = nested.get(
                "scenes",
                []
            )

            if isinstance(
                scenes,
                list
            ):

                return scenes

        return []

    # =========================================================
    # NORMALIZE SCENE LIST
    # =========================================================

    def _normalize_scene_list(
        self,
        scenes,
        sequence,
        characters,
        environments,
        props,
        starting_scene,
        expected_count
    ):

        result = []

        act_number = self._safe_int(
            sequence.get(
                "act_number",
                0
            ),
            0
        )

        act_title = str(
            sequence.get(
                "act_title",
                ""
            )
            or ""
        )

        sequence_number = self._safe_int(
            sequence.get(
                "number",
                0
            ),
            0
        )

        sequence_title = str(
            sequence.get(
                "title",
                ""
            )
            or ""
        )

        # -----------------------------------------------------
        # Only requested number is accepted.
        # -----------------------------------------------------

        scenes = scenes[
            :expected_count
        ]

        for index, scene in enumerate(
            scenes
        ):

            if not isinstance(
                scene,
                dict
            ):

                continue

            number = (
                starting_scene
                + index
            )

            normalized = {

                "number":
                    number,

                "act_number":
                    act_number,

                "act_title":
                    act_title,

                "sequence_number":
                    sequence_number,

                "sequence_title":
                    sequence_title,

                "title":
                    self._clean_text(
                        scene.get(
                            "title",
                            ""
                        )
                    )
                    or f"Scene {number}",

                "purpose":
                    self._clean_text(
                        scene.get(
                            "purpose",
                            ""
                        )
                    ),

                "script":
                    self._clean_text(
                        scene.get(
                            "script",
                            ""
                        )
                    ),

                "characters":
                    self._clean_name_list(
                        scene.get(
                            "characters",
                            []
                        )
                    ),

                "character_references":
                    [],

                "environment":
                    self._clean_text(
                        scene.get(
                            "environment",
                            ""
                        )
                    ),

                "environment_references":
                    [],

                "props":
                    self._clean_name_list(
                        scene.get(
                            "props",
                            []
                        )
                    ),

                "prop_references":
                    [],

                "costumes":
                    self._clean_name_list(
                        scene.get(
                            "costumes",
                            []
                        )
                    ),

                "action":
                    self._clean_text(
                        scene.get(
                            "action",
                            ""
                        )
                    ),

                "dialogue":
                    self._clean_text(
                        scene.get(
                            "dialogue",
                            ""
                        )
                    ),

                "image_prompt":
                    self._clean_text(
                        scene.get(
                            "image_prompt",
                            ""
                        )
                    ),

                "video_prompt":
                    self._clean_text(
                        scene.get(
                            "video_prompt",
                            ""
                        )
                    ),

                "duration":
                    max(
                        1,
                        self._safe_int(
                            scene.get(
                                "duration",
                                5
                            ),
                            5
                        )
                    ),

                "previous_scene_number":
                    (
                        number - 1
                        if index > 0
                        else 0
                    ),

                "next_scene_number":
                    (
                        number + 1
                        if index < len(scenes) - 1
                        else 0
                    ),

                "continuity_notes":
                    self._clean_text(
                        scene.get(
                            "continuity_notes",
                            ""
                        )
                    ),

                "status":
                    self._clean_text(
                        scene.get(
                            "status",
                            "Planned"
                        )
                    )
                    or "Planned"
            }

            result.append(
                normalized
            )

        return result

    # =========================================================
    # CLEAN TEXT
    # =========================================================

    @staticmethod
    def _clean_text(
        value
    ):

        if value is None:
            return ""

        if isinstance(
            value,
            str
        ):

            return value.strip()

        return str(
            value
        ).strip()

    # =========================================================
    # CLEAN NAME LIST
    # =========================================================

    def _clean_name_list(
        self,
        value
    ):

        values = self._ensure_list(
            value
        )

        result = []

        for item in values:

            if isinstance(
                item,
                str
            ):

                name = item.strip()

                if name:

                    result.append(
                        name
                    )

            elif isinstance(
                item,
                dict
            ):

                name = self._extract_name(
                    item
                )

                if name:

                    result.append(
                        name
                    )

        return self._deduplicate(
            result
        )

    # =========================================================
    # ENSURE LIST
    # =========================================================

    @staticmethod
    def _ensure_list(
        value
    ):

        if value is None:
            return []

        if isinstance(
            value,
            list
        ):

            return value

        if isinstance(
            value,
            tuple
        ):

            return list(
                value
            )

        if isinstance(
            value,
            str
        ):

            if not value.strip():

                return []

            return [
                value
            ]

        return [
            value
        ]

    # =========================================================
    # DEDUPLICATE
    # =========================================================

    @staticmethod
    def _deduplicate(
        values
    ):

        result = []

        seen = set()

        for value in values:

            try:

                key = json.dumps(
                    value,
                    sort_keys=True,
                    default=str
                )

            except Exception:

                key = str(
                    value
                )

            if key in seen:
                continue

            seen.add(
                key
            )

            result.append(
                value
            )

        return result

    # =========================================================
    # NORMALIZE NAME
    # =========================================================

    @staticmethod
    def _normalize_name(
        value
    ):

        return re.sub(
            r"\s+",
            " ",
            str(
                value
            ).strip().lower()
        )

    # =========================================================
    # SAFE INTEGER
    # =========================================================

    @staticmethod
    def _safe_int(
        value,
        default=0
    ):

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return default

    # =========================================================
    # JSON TEXT
    # =========================================================

    @staticmethod
    def _json_text(
        value
    ):

        try:

            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str
            )

        except Exception:

            return str(
                value
            )

    # =========================================================
    # JSON PARSER
    # =========================================================

    @staticmethod
    def _parse_json(
        raw_data
    ):

        if isinstance(
            raw_data,
            (
                dict,
                list
            )
        ):

            return raw_data

        text = str(
            raw_data
        ).strip()

        if not text:

            raise ValueError(
                "Empty AI response."
            )

        # -----------------------------------------------------
        # Remove code fences
        # -----------------------------------------------------

        text = re.sub(
            r"^\s*```json\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"^\s*```\s*",
            "",
            text
        )

        text = re.sub(
            r"\s*```\s*$",
            "",
            text
        )

        text = text.strip()

        # -----------------------------------------------------
        # Direct JSON
        # -----------------------------------------------------

        try:

            return json.loads(
                text
            )

        except json.JSONDecodeError:

            pass

        # -----------------------------------------------------
        # JSON OBJECT
        # -----------------------------------------------------

        object_start = text.find(
            "{"
        )

        object_end = text.rfind(
            "}"
        )

        if (
            object_start != -1
            and object_end > object_start
        ):

            candidate = text[
                object_start:
                object_end + 1
            ]

            try:

                return json.loads(
                    candidate
                )

            except json.JSONDecodeError:

                pass

        # -----------------------------------------------------
        # JSON ARRAY
        # -----------------------------------------------------

        array_start = text.find(
            "["
        )

        array_end = text.rfind(
            "]"
        )

        if (
            array_start != -1
            and array_end > array_start
        ):

            candidate = text[
                array_start:
                array_end + 1
            ]

            try:

                return json.loads(
                    candidate
                )

            except json.JSONDecodeError:

                pass

        raise ValueError(
            "No valid JSON object or array found "
            "in AI response."
        )

    # =========================================================
    # OBJECT → DICT
    # =========================================================

    @staticmethod
    def _to_dict(
        value
    ):

        if value is None:

            return {}

        if isinstance(
            value,
            dict
        ):

            return dict(
                value
            )

        if hasattr(
            value,
            "__dict__"
        ):

            try:

                return dict(
                    vars(value)
                )

            except Exception:

                pass

        result = {}

        for key in dir(value):

            if key.startswith("_"):
                continue

            try:

                item = getattr(
                    value,
                    key
                )

            except Exception:

                continue

            if callable(item):
                continue

            result[key] = item

        return result