from pydantic import BaseModel


class CharacterRequest(BaseModel):

    description: str

    style: str = "Cinematic"


class Character(BaseModel):

    name: str
    role: str
    gender: str
    age: str
    appearance: str
    costume: str
    accessories: str
    hairstyle: str
    face: str
    eyes: str
    body: str
    personality: str
    powers: str
    style: str
    negative_prompt: str


class CharacterResponse(BaseModel):

    character: Character
