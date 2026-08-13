from pydantic import BaseModel


class SceneRequest(BaseModel):

    script: str


class Scene(BaseModel):

    number: int

    title: str

    script: str

    duration: int


class SceneResponse(BaseModel):

    scenes: list[Scene]
