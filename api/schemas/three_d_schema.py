from pydantic import BaseModel, Field


class ThreeDRequest(BaseModel):

    image: str

    asset_id: str = "matangi_asset"

    resolution: int = Field(
        default=3072,
        ge=1,
        le=8192
    )

    batch_size: int = Field(
        default=1,
        ge=1,
        le=4
    )

    seed: int = -1

    steps: int = Field(
        default=30,
        ge=1,
        le=100
    )

    cfg: float = Field(
        default=5.0,
        ge=0.0,
        le=20.0
    )

    octree_resolution: int = Field(
        default=256,
        ge=16,
        le=512
    )

    threshold: float = Field(
        default=0.6,
        ge=-1.0,
        le=1.0
    )
