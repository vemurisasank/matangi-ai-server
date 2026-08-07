from pydantic import BaseModel


class PromptRequest(BaseModel):

    script: str

    style: str = "Cinematic"

    language: str = "English"

    scene_count: int = 5

class ScenePrompt(BaseModel):

    scene: int

    title: str

    environment: str

    character: str

    camera: str

    lighting: str

    mood: str

    image_prompt: str


class PromptResponse(BaseModel):

    scenes: list[ScenePrompt]