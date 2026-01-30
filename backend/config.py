import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    MAX_DAILY_HOURS: float = 8.0
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-dev")
    # Prioritize PORT from env (Render/Heroku standard)
    BACKEND_PORT: int = int(os.getenv("PORT", 8000))
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    
settings = Settings()
