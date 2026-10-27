from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "ContentIQ Backend API"
    API_V1_PREFIX: str = "/api/v1"
    VERSION: str = "1.0.0"

    # Security
    SECRET_KEY: str = "dev-secret-key-contentiq-ai-platform-2026-auth-token-super-safe"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    INTEGRATION_ENCRYPTION_KEY: str = ""  # 32-byte Fernet key, auto-derived from SECRET_KEY if empty

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "contentiq_db"
    DATABASE_URL: Union[str, None] = None

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            # Normalize to asyncpg if user gave standard postgresql://
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        async_url = self.async_database_url
        if "postgresql+asyncpg://" in async_url:
            return async_url.replace("postgresql+asyncpg://", "postgresql://")
        if "sqlite+aiosqlite:///" in async_url:
            return async_url.replace("sqlite+aiosqlite:///", "sqlite:///")
        return async_url

    # Logging
    LOG_LEVEL: str = "INFO"

    # ── Media analysis settings ───────────────────────────────
    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Private media upload storage (absolute path or relative to CWD)
    MEDIA_UPLOAD_DIR: str = "./uploads/media"

    # Per-type size limits (MB)
    MEDIA_MAX_IMAGE_MB: int = 20
    MEDIA_MAX_AUDIO_MB: int = 100
    MEDIA_MAX_VIDEO_MB: int = 500

    # Detector adapter selection — must match an adapter backend key
    # Set to empty string if not configured (adapter will report INCONCLUSIVE)
    IMAGE_DETECTOR: str = ""          # "hive" | "sightengine"
    AUDIO_DETECTOR: str = ""          # "elevenlabs_detect" | "hive_audio"
    VIDEO_DETECTOR: str = ""          # "hive_video" | "microsoft_video"

    # Provider API keys (leave blank if adapter not used)
    HIVE_API_KEY: str = ""
    SIGHTENGINE_USER: str = ""
    SIGHTENGINE_SECRET: str = ""
    ELEVENLABS_API_KEY: str = ""
    AZURE_VIDEO_INDEXER_KEY: str = ""
    AZURE_VIDEO_INDEXER_ACCOUNT_ID: str = ""
    AZURE_VIDEO_INDEXER_LOCATION: str = "trial"

    # Optional AV consistency check via ffprobe
    AV_CONSISTENCY_CHECK: bool = False
    FFPROBE_PATH: str = "ffprobe"

    # ── Rubric Evaluator Settings ──────────────────────────────
    LLM_EVALUATOR_API_KEY: str = ""
    LLM_EVALUATOR_PROVIDER: str = "openai"  # "openai" | "anthropic" | "gemini"
    LLM_EVALUATOR_MODEL: str = "gpt-4o"
    LLM_EVALUATOR_TIMEOUT_SECONDS: int = 30


settings = Settings()
