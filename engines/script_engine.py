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

        provider = server.provider_manager.get(
            "ollama"
        )

        # =====================================================
        # NORMAL SCRIPT GENERATION
        # =====================================================

        if task == "script":

            prompt = f"""
You are a professional cinematic screenplay writer.

Create a detailed screenplay based on the information below.

TITLE:
{title}

DESCRIPTION:
{description}

STYLE:
{style}

LANGUAGE:
{language}

REQUIREMENTS:

1. Write the screenplay in the requested language.
2. Structure the screenplay into clear scenes.
3. Include scene descriptions.
4. Include character actions and dialogue where appropriate.
5. Maintain cinematic storytelling.
6. Respect the requested visual style.
7. Do not explain your process.
8. Return ONLY the screenplay.
"""

        # =====================================================
        # ACT STORY GENERATION
        # =====================================================

        elif task == "act_story":

            prompt = f"""
You are the story architect for a feature-length cinematic movie.

You are developing the detailed story architecture of ONE ACT.

You are NOT writing the final screenplay.

You are NOT generating individual numbered scenes.

You must develop ONLY the requested act.

ACT REQUEST:

{description}

TITLE:
{title}

STYLE:
{style}

LANGUAGE:
{language}

IMPORTANT:

Develop the complete narrative progression of this act.

The act must have:

BEGINNING
MIDDLE
ESCALATION
TURNING POINT
ENDING

Include:

- character goals
- character development
- relationships
- conflicts
- sub-conflicts
- locations
- important props
- important events
- emotional progression
- visual opportunities
- dialogue opportunities
- reveals
- turning points
- cause and effect
- continuity
- consequences
- setup for the following act

Do NOT summarize the entire movie.

Do NOT generate numbered scenes.

Do NOT write:

Scene 1
Scene 2
Scene 3

Return ONLY the detailed story of this act.
"""

        # =====================================================
        # SEQUENCE STORY GENERATION
        # =====================================================

        elif task == "sequence_story":

            prompt = f"""
You are the story architect for a feature-length cinematic movie.

You are developing the detailed story architecture of ONE SEQUENCE.

You are NOT writing the final screenplay.

You are NOT generating individual numbered scenes.

You must develop ONLY the requested sequence.

SEQUENCE REQUEST:

{description}

TITLE:
{title}

STYLE:
{style}

LANGUAGE:
{language}

IMPORTANT:

The sequence must form a continuous chronological progression.

It must contain enough story material to later create
individual cinematic scenes.

Include:

1. Sequence opening
2. Character objectives
3. Character actions
4. Character motivations
5. Character relationships
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
17. Sequence climax
18. Sequence ending
19. Setup for the following sequence
20. Continuity requirements

CRITICAL:

Do NOT restart the story.

Do NOT repeat events that have already happened.

Advance the story from the supplied continuity information.

Do NOT summarize the entire movie.

Do NOT generate numbered scenes.

Do NOT write:

Scene 1
Scene 2
Scene 3

Return ONLY the detailed story of this sequence.
"""

        # =====================================================
        # UNKNOWN TASK
        # =====================================================

        else:

            return {
                "success": False,
                "message": f"Unknown script generation task: {task}"
            }

        # =====================================================
        # CALL OLLAMA
        # =====================================================

        result = provider.generate(
            prompt,
            validate_prompt=False
        )

        if not result.get("success"):

            return result

        # =====================================================
        # FINAL RESPONSE
        # =====================================================

        return {
            "success": True,
            "provider": "Ollama",
            "data": result.get(
                "output",
                ""
            )
        }