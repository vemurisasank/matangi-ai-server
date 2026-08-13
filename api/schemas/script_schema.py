from pydantic import BaseModel


class ScriptRequest(BaseModel):

    title: str = ""

    description: str

    style: str = "Cinematic"

    language: str = "English"
