from pydantic import BaseModel, Field


class SceneRequest(BaseModel):

    script: str = ""

    sequence_story: str = ""

    sequence_title: str = ""

    scene_count: int = 10

    act_number: int = 0

    sequence_number: int = 0

    movie_description: str = ""

    style: str = "Cinematic"

    language: str = "English"

    characters: list = Field(
        default_factory=list
    )

    environments: list = Field(
        default_factory=list
    )

    props: list = Field(
        default_factory=list
    )

    previous_scenes: list = Field(
        default_factory=list
    )

    previous_sequence_summaries: list = Field(
        default_factory=list
    )

    continuity_context: str = ""


class Scene(BaseModel):

    number: int

    title: str

    purpose: str = ""

    script: str

    characters: list = Field(
        default_factory=list
    )

    environment: str = ""

    props: list = Field(
        default_factory=list
    )

    costumes: list = Field(
        default_factory=list
    )

    action: str = ""

    dialogue: str = ""

    image_prompt: str = ""

    video_prompt: str = ""

    duration: int = 5


class SceneResponse(BaseModel):

    scenes: list[Scene]