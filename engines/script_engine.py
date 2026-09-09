from core.server_context import server


class ScriptEngine:

    @staticmethod
    def generate(
        title,
        description,
        style="Cinematic",
        language="English",
        task="script"
    ):

        provider = server.provider_manager.get("ollama")

        # =====================================================
        # NORMAL SMALL SCRIPT
        # =====================================================

        if task == "script":

            prompt = f"""
You are a professional cinematic screenplay writer
for MATANGI AI STUDIO.

Create a concise, production-ready screenplay.

TITLE:
{title}

DESCRIPTION:
{description}

STYLE:
{style}

LANGUAGE:
{language}

IMPORTANT:

This is the SMALL SCRIPT mode.

It is intended for advertisements, short films,
social media videos and other short productions.

Do not create a 60-minute movie.

Create a practical screenplay with approximately
3 to 12 scenes depending on the supplied story.

Each scene should contain:

- Scene number
- Location
- Time
- Action
- Characters
- Dialogue
- Visual direction

Keep the story concise and coherent.

Return ONLY the screenplay.
"""

        # =====================================================
        # MOVIE STRUCTURE EXTRACTION
        # =====================================================

        elif task == "movie_structure":

            master_script = description

            prompt = f"""
You are the MOVIE STRUCTURE ANALYZER for
MATANGI AI STUDIO.

Your task is to analyze the COMPLETE MASTER SCREENPLAY
supplied below.

You are NOT writing a new story.

You are NOT inventing a new movie.

You must extract the EXISTING story structure.

=========================================================
MASTER SCREENPLAY
=========================================================

{master_script}

=========================================================
MOVIE INFORMATION
=========================================================

TITLE:
{title}

STYLE:
{style}

LANGUAGE:
{language}

=========================================================
OBJECTIVE
=========================================================

Extract:

MOVIE
  ↓
ACTS
  ↓
SEQUENCES

The screenplay may contain:

- Act headings
- Sequence headings
- Scene headings
- INT / EXT
- locations
- time of day
- numbered scenes
- unnumbered scenes

Recognize the structure even when formatting is
not perfectly standardized.

=========================================================
CRITICAL STORY RULE
=========================================================

Use ONLY information contained in the master screenplay.

Do NOT invent:

- new acts
- new sequences
- new characters
- new locations
- new events
- new mythology
- new story elements

If the screenplay does not explicitly contain an
Act or Sequence heading, infer the smallest reasonable
structural grouping from the screenplay itself.

Do not invent story content while doing this.

=========================================================
LONG-FORM TARGET
=========================================================

The target production format is approximately:

60 minutes
approximately 200 scenes

However, DO NOT artificially create 200 scenes here.

This stage only extracts the existing story structure.

The Scene Planner will later divide the actual story
into individual production scenes.

=========================================================
SEQUENCE INFORMATION
=========================================================

For every sequence provide:

- act_number
- act_title
- sequence_number
- title
- description
- purpose
- location
- characters
- important_events
- emotional_progression
- visual_opportunities
- continuity_notes
- scene_count
- starting_scene_number
- ending_scene_number

Scene numbers must be GLOBAL across the movie.

=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON.

Use this structure:

{{
    "movie": {{
        "title": "{title}",
        "description": "",
        "style": "{style}",
        "language": "{language}",
        "duration_minutes": 60,
        "target_scene_count": 200
    }},
    "acts": [
        {{
            "act_number": 1,
            "title": "",
            "description": "",
            "purpose": "",
            "beginning": "",
            "middle": "",
            "escalation": "",
            "turning_point": "",
            "ending": "",
            "sequence_count": 0,
            "sequences": [
                {{
                    "act_number": 1,
                    "act_title": "",
                    "sequence_number": 1,
                    "title": "",
                    "description": "",
                    "purpose": "",
                    "location": "",
                    "characters": [],
                    "important_events": [],
                    "emotional_progression": "",
                    "visual_opportunities": [],
                    "continuity_notes": "",
                    "scene_count": 0,
                    "starting_scene_number": 1,
                    "ending_scene_number": 1
                }}
            ]
        }}
    ]
}}

IMPORTANT:

scene_count must represent the approximate number of
production scenes that can be developed from the
actual sequence story.

Do not simply assign 10 scenes to every sequence.

Calculate it from the amount of actual story material.

Return ONLY JSON.
"""

        # =====================================================
        # ACT STORY
        # =====================================================

        elif task == "act_story":

            prompt = f"""
You are the story architect for MATANGI AI STUDIO.

Develop ONLY the requested ACT using the supplied story.

TITLE:
{title}

STYLE:
{style}

LANGUAGE:
{language}

ACT REQUEST:
{description}

Do NOT write the final screenplay.

Do NOT generate numbered scenes.

Preserve the supplied story exactly.

Include:

- beginning
- middle
- escalation
- turning point
- ending
- character goals
- conflicts
- important events
- locations
- props
- emotional progression
- reveals
- consequences
- continuity
- setup for the next act

Do not invent unrelated story elements.

Return ONLY the detailed act story.
"""

        # =====================================================
        # SEQUENCE STORY
        # =====================================================

        elif task == "sequence_story":

            prompt = f"""
You are the sequence story architect for
MATANGI AI STUDIO.

Develop ONLY the requested sequence.

TITLE:
{title}

STYLE:
{style}

LANGUAGE:
{language}

SEQUENCE REQUEST:
{description}

Do NOT write numbered scenes.

Do NOT create a different story.

Develop the actual supplied sequence into enough
cinematic story detail for a Scene Planner to later
create individual scenes.

Include:

1. Opening
2. Character objectives
3. Character actions
4. Motivations
5. Relationships
6. Conflict
7. Escalation
8. Important events
9. Locations
10. Props
11. Dialogue opportunities
12. Emotional progression
13. Visual moments
14. Reveals
15. Cause and effect
16. Turning point
17. Climax
18. Ending
19. Setup for following sequence
20. Continuity requirements

Return ONLY the detailed sequence story.
"""

        else:

            return {
                "success": False,
                "message": f"Unknown script generation task: {task}"
            }

        # =====================================================
        # OLLAMA
        # =====================================================

        validation_type = (
            "movie_structure"
            if task == "movie_structure"
            else None
        )

        result = provider.generate(
            prompt,
            validate_prompt=False,
            validation_type=validation_type
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