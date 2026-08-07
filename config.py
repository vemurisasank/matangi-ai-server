from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str = "MATANGI AI SERVER"

    VERSION: str = "1.0.0"

    DEBUG: bool = True

    HOST: str = "127.0.0.1"

    PORT: int = 8000


settings = Settings()