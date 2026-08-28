from typing import Any, Dict

from pydantic import BaseModel, Field


# =========================================================
# NORMAL ENVIRONMENT
# =========================================================

class EnvironmentRequest(BaseModel):

    description: str = ""

    style: str = "Cinematic"


# =========================================================
# MASTER SCRIPT ENVIRONMENT EXTRACTION
# =========================================================

class EnvironmentExtractionRequest(BaseModel):

    script: str = ""

    style: str = "Cinematic"

    language: str = "English"


# =========================================================
# ENVIRONMENT PROFILE
# =========================================================

class EnvironmentProfileRequest(BaseModel):

    environment: Dict[str, Any] = Field(
        default_factory=dict
    )

    master_script: str = ""

    style: str = "Cinematic"


# =========================================================
# ENVIRONMENT CONCEPTS
# =========================================================

class EnvironmentConceptRequest(BaseModel):

    environment: Dict[str, Any] = Field(
        default_factory=dict
    )

    style: str = "Cinematic"