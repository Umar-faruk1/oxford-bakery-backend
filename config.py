from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Server Configuration
    HOST: str
    PORT: int
    BACKEND_URL: str

    # Database Configuration
    DATABASE_URL: str

    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # CORS Configuration
    ALLOWED_ORIGINS: str

    # File Upload Configuration
    UPLOAD_DIR: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 