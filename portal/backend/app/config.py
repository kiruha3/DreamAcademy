from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    MOODLE_URL: str = "http://localhost:8080"
    MOODLE_TOKEN: str = ""

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
