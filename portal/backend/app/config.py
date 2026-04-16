from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    MOODLE_URL: str = "http://localhost:8080"
    MOODLE_PUBLIC_URL: str = "http://localhost:8080"
    MOODLE_TOKEN: str = ""
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = {"env_file": ".env", "extra": "ignore"}

@lru_cache()
def get_settings() -> Settings:
    return Settings()
