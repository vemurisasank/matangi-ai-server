from fastapi import APIRouter

from api.schemas.environment_schema import (
    EnvironmentRequest,
    EnvironmentExtractionRequest,
    EnvironmentProfileRequest,
    EnvironmentConceptRequest
)

from engines.environment_engine import EnvironmentEngine

from core.response_manager import ResponseManager


router = APIRouter()


# =========================================================
# NORMAL ENVIRONMENT
# =========================================================

@router.post("/environment")
def generate_environment(
    request: EnvironmentRequest
):

    try:

        result = EnvironmentEngine.generate(
            request
        )

        return result

    except Exception as e:

        return ResponseManager.failure(
            str(e)
        )


# =========================================================
# ENVIRONMENT EXTRACTION
# =========================================================

@router.post("/environment/extract")
def extract_environments(
    request: EnvironmentExtractionRequest
):

    try:

        result = EnvironmentEngine.extract(
            request
        )

        return result

    except Exception as e:

        return ResponseManager.failure(
            str(e)
        )


# =========================================================
# ENVIRONMENT PROFILE
# =========================================================

@router.post("/environment/profile")
def generate_environment_profile(
    request: EnvironmentProfileRequest
):

    try:

        result = EnvironmentEngine.profile(
            request
        )

        return result

    except Exception as e:

        return ResponseManager.failure(
            str(e)
        )


# =========================================================
# ENVIRONMENT CONCEPTS
# =========================================================

@router.post("/environment/concepts")
def generate_environment_concepts(
    request: EnvironmentConceptRequest
):

    try:

        result = EnvironmentEngine.concepts(
            request
        )

        return result

    except Exception as e:

        return ResponseManager.failure(
            str(e)
        )