from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from config.constants import APP_NAME, VERSION

from core.logger import Logger
from core.exception_manager import ExceptionManager
from core.bootstrap_manager import BootstrapManager

from api.routes.models import router as model_router
from api.routes.providers import router as provider_router
from api.routes.jobs import router as jobs_router
from api.routes.script import router as script_router
from api.routes.prompt import router as prompt_router
from api.routes.scene import router as scene_router
from api.routes.character import router as character_router
from api.routes.environment import router as environment_router
from api.routes.image import router as image_router
from api.routes.voice import router as voice_router
from api.routes.music import router as music_router
from api.routes.video import router as video_router
from api.routes.render import router as render_router
from api.routes.health import router as health_router
from api.routes.upload import router as upload_router
from api.routes.three_d import router as three_d_router


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app):

    BootstrapManager.initialize()

    Logger.info("=" * 60)
    Logger.info("MATANGI AI SERVER STARTED")
    Logger.info("=" * 60)

    yield

    Logger.info("=" * 60)
    Logger.info("MATANGI AI SERVER STOPPED")
    Logger.info("=" * 60)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    lifespan=lifespan
)


# =========================================================
# EXCEPTION HANDLER
# =========================================================

app.add_exception_handler(
    Exception,
    ExceptionManager.handle_exception
)


# =========================================================
# STATIC OUTPUT DIRECTORIES
# =========================================================

AUDIO_DIR = (
    "/workspace/matangi-ai-server/outputs/audio"
)

THREE_D_DIR = (
    "/workspace/matangi-ai-server/outputs/3d"
)


app.mount(
    "/audio",
    StaticFiles(
        directory=AUDIO_DIR
    ),
    name="audio"
)


app.mount(
    "/3d",
    StaticFiles(
        directory=THREE_D_DIR
    ),
    name="3d"
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "success": True,
        "message": f"{APP_NAME} Running",
        "version": VERSION
    }


# =========================================================
# HEALTH
# =========================================================

app.include_router(
    health_router,
    tags=["Health"]
)


# =========================================================
# MODELS
# =========================================================

app.include_router(
    model_router,
    tags=["Models"]
)


# =========================================================
# PROVIDERS
# =========================================================

app.include_router(
    provider_router,
    tags=["Providers"]
)


# =========================================================
# JOBS
# =========================================================

app.include_router(
    jobs_router,
    tags=["Jobs"]
)


# =========================================================
# SCRIPT
# =========================================================

app.include_router(
    script_router,
    tags=["Script"]
)


# =========================================================
# PROMPT
# =========================================================

app.include_router(
    prompt_router,
    tags=["Prompt"]
)


# =========================================================
# SCENE
# =========================================================

app.include_router(
    scene_router,
    tags=["Scene"]
)


# =========================================================
# CHARACTER
# =========================================================

app.include_router(
    character_router,
    tags=["Character"]
)


# =========================================================
# ENVIRONMENT
# =========================================================

app.include_router(
    environment_router,
    tags=["Environment"]
)


# =========================================================
# IMAGE
# =========================================================

app.include_router(
    image_router,
    tags=["Image"]
)


# =========================================================
# 3D
# =========================================================

app.include_router(
    three_d_router,
    tags=["3D"]
)


# =========================================================
# VOICE
# =========================================================

app.include_router(
    voice_router,
    tags=["Voice"]
)


# =========================================================
# MUSIC
# =========================================================

app.include_router(
    music_router,
    tags=["Music"]
)


# =========================================================
# VIDEO
# =========================================================

app.include_router(
    video_router,
    tags=["Video"]
)


# =========================================================
# RENDER
# =========================================================

app.include_router(
    render_router,
    tags=["Render"]
)


# =========================================================
# UPLOAD
# =========================================================

app.include_router(
    upload_router,
    tags=["Upload"]
)
