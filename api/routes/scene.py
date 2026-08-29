from fastapi import APIRouter

from engines.scene_planner_engine import (
    ScenePlannerEngine
)

from core.response_manager import ResponseManager


router = APIRouter()


@router.post("/scene-plan")
def generate_scene_plan(request: dict):

    try:

        planner = ScenePlannerEngine()

        sequence_data = request.get(
            "sequence",
            {}
        )

        # -----------------------------------------------------
        # Convert dictionary to simple object
        # -----------------------------------------------------

        class SequenceObject:
            pass

        sequence = SequenceObject()

        for key, value in sequence_data.items():

            setattr(
                sequence,
                key,
                value
            )

        result = planner.generate_scene_plans(

            sequence=sequence,

            movie_description=request.get(
                "movie_description",
                ""
            ),

            master_script=request.get(
                "master_script",
                ""
            ),

            style=request.get(
                "style",
                "Cinematic"
            ),

            language=request.get(
                "language",
                "English"
            ),

            characters=request.get(
                "characters",
                []
            ),

            environments=request.get(
                "environments",
                []
            ),

            props=request.get(
                "props",
                []
            ),

            previous_scenes=request.get(
                "previous_scenes",
                []
            ),

            previous_sequence_summaries=request.get(
                "previous_sequence_summaries",
                []
            ),

            continuity_context=request.get(
                "continuity_context",
                ""
            )

        )

        if not result.get(
            "success",
            False
        ):

            return ResponseManager.failure(
                result.get(
                    "message",
                    "Scene planning failed."
                )
            )

        return ResponseManager.success(

            result.get(
                "data",
                {}
            ),

            "Scene Plans Generated Successfully"

        )

    except Exception as error:

        return ResponseManager.failure(
            str(error)
        )