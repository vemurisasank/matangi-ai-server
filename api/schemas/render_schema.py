from pydantic import BaseModel


class RenderRequest(BaseModel):

    project_id: str

    quality: str = "High"

    resolution: str = "1920x1080"

    fps: int = 24