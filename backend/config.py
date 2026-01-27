import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    MAX_DAILY_HOURS: float = 8.0
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-dev")
    BACKEND_PORT: int = 8000
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # SMTP Config
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 465))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SYSTEM_EMAIL: str = os.getenv("SYSTEM_EMAIL", "")
    
settings = Settings()
