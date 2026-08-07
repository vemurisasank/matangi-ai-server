from fastapi import FastAPI
from config.settings import settings
from contextlib import asynccontextmanager
from core.logger import Logger
from core.exception_manager import ExceptionManager
from api.routes.models import router as model_router
from api.routes.providers import router as provider_router
from core.bootstrap_manager import BootstrapManager
from api.routes.jobs import router as jobs_router
from api.routes.script import router as script_router
from api.routes.prompt import router as prompt_router
from api.routes.image import router as image_router
from api.routes.voice import router as voice_router
from api.routes.music import router as music_router
from api.routes.video import router as video_router
from api.routes.render import router as render_router
from api.routes.health import router as health_router
from config.constants import APP_NAME, VERSION


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

app = FastAPI(

    title=APP_NAME,

    version=VERSION,

    lifespan=lifespan

)

app.include_router(

    health_router,

    tags=["Health"]

)


@app.get("/")

def root():

    return {

        "success": True,

        "message": f"{APP_NAME} Running"

    }
@asynccontextmanager
async def lifespan(app):

    Logger.setup()

    Logger.info("Application Started")

    yield

    Logger.info("Application Closed")

app.add_exception_handler(

    Exception,

    ExceptionManager.handle_exception

)

app.include_router(

    model_router,

    tags=["Models"]

)

app.include_router(

    provider_router,

    tags=["Providers"]

)

app.include_router(

    jobs_router,

    tags=["Jobs"]

)

app.include_router(

    script_router,

    tags=["Script"]

)

app.include_router(

    prompt_router,

    tags=["Prompt"]

)


app.include_router(

    image_router,

    tags=["Image"]

)
app.include_router(voice_router, tags=["Voice"])
app.include_router(music_router, tags=["Music"])
app.include_router(video_router, tags=["Video"])
app.include_router(render_router, tags=["Render"])


app.include_router(

    health_router,

    tags=["Health"]
)