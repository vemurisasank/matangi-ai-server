from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    VERSION: str

    HOST: str
    PORT: int
    DEBUG: bool

    OLLAMA_HOST: str
    COMFYUI_HOST: str

    TEXT_MODEL: str
    IMAGE_WORKFLOW: str

    VIDEO_MODEL: str
    VOICE_MODEL: str
    MUSIC_MODEL: str

    LOG_LEVEL: str

    PROJECT_PATH: str
    OUTPUT_PATH: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
