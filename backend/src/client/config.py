from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientSettings(BaseSettings):
    """Centralized client and application configuration for DocPilot."""
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    # JWT Authentication
    SECRET_KEY: str = "docpilot-secure-dev-secret-key-at-least-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Supabase Client Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # Service role key or main API key
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: str = ""


    # OpenRouter LLM Client Configuration
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"

    # Walrus Memory Subsystem Configuration
    WALRUS_ENABLED: bool = True
    WALRUS_ENV: str = "dev"
    WALRUS_DELEGATE_KEY: str = ""
    WALRUS_ACCOUNT_ID: str = ""
    WALRUS_SERVER_URL: str = "https://relayer.dev.walrus.space"

    # Telegram Bot API Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_SECRET_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Client settings singleton instance
settings = ClientSettings()
# Alias for backwards compatibility
client_settings = settings
