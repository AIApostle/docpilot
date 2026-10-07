from typing import List, Optional
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientSettings(BaseSettings):
    """Centralized client and application configuration for DocPilot."""
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    # JWT Authentication
    SECRET_KEY: str = Field(
        default="docpilot-local-dev-secret-change-me",
        description="Secret used to sign app-issued JWTs. Override in environment for non-local deployments.",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

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
    WALRUS_DELEGATE_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("MEMWAL_PRIVATE_KEY", "WALRUS_DELEGATE_KEY"),
    )
    WALRUS_ACCOUNT_ID: str = Field(
        default="",
        validation_alias=AliasChoices("MEMWAL_ACCOUNT_ID", "WALRUS_ACCOUNT_ID"),
    )
    WALRUS_SERVER_URL: str = Field(
        default="https://relayer.dev.memwal.ai",
        validation_alias=AliasChoices("MEMWAL_SERVER_URL", "WALRUS_SERVER_URL"),
    )
    WALRUS_VERIFY: bool = Field(
        default=False,
        validation_alias=AliasChoices("MEMWAL_VERIFY", "WALRUS_VERIFY"),
    )

    # Telegram Bot API Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = "docpilot_AIbot"
    TELEGRAM_SECRET_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime_security(self):
        env = (self.ENVIRONMENT or "").lower()
        default_dev_secrets = {
            "docpilot-local-dev-secret-change-me",
            "docpilot-secure-dev-secret-key-at-least-32-characters",
        }
        if env in {"production", "prod"} and self.SECRET_KEY in default_dev_secrets:
            raise ValueError("SECRET_KEY must be configured with a non-default secret in production.")
        return self


# Client settings singleton instance
settings = ClientSettings()
# Alias for backwards compatibility
client_settings = settings
