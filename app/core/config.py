import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # App
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # Webhook (global fallback)
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")

    # Sessions directory
    SESSIONS_DIR: str = os.getenv("SESSIONS_DIR", "sessions")


settings = Settings()
