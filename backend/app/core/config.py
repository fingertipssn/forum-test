from pydantic_settings import BaseSettings
from typing import List
import json
import logging
import secrets

logger = logging.getLogger(__name__)

_INSECURE_DEFAULT_SECRET = "discourse-dev-secret-change-in-production"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://discourse:discourse@localhost:5432/discourse"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://discourse:discourse@localhost:5432/discourse"

    AZURE_AD_TENANT_ID: str = ""
    AZURE_AD_CLIENT_ID: str = ""
    AZURE_AD_AUDIENCE: str = ""

    APP_NAME: str = "Discourse Forum"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    CORS_ORIGINS: str = '["http://localhost:4200"]'

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    UPLOADS_PATH: str = "./uploads"
    SITE_BASE_URL: str = "http://localhost:8000"

    DEV_MODE: bool = False
    DEV_JWT_SECRET: str = _INSECURE_DEFAULT_SECRET

    CELERY_ENABLED: bool = True

    MAX_POST_LENGTH: int = 32000
    MAX_TOPIC_TITLE_LENGTH: int = 255
    MIN_TOPIC_TITLE_LENGTH: int = 15
    POSTS_PER_PAGE: int = 20
    TOPICS_PER_PAGE: int = 30

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    @property
    def jwks_uri(self) -> str:
        return f"https://login.microsoftonline.com/{self.AZURE_AD_TENANT_ID}/discovery/v2.0/keys"

    @property
    def azure_issuer(self) -> str:
        return f"https://login.microsoftonline.com/{self.AZURE_AD_TENANT_ID}/v2.0"

    model_config = {"env_file": ".env"}


settings = Settings()

if not settings.DEV_MODE and settings.DEV_JWT_SECRET == _INSECURE_DEFAULT_SECRET:
    raise RuntimeError(
        "DEV_JWT_SECRET must be changed from the default value before running in production. "
        f"Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

if settings.DEV_MODE and settings.DEV_JWT_SECRET == _INSECURE_DEFAULT_SECRET:
    logger.warning(
        "DEV_JWT_SECRET is set to the insecure default. "
        "Set a strong secret via the DEV_JWT_SECRET environment variable."
    )
