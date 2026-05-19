from pydantic_settings import BaseSettings
from typing import List
import json


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
    DEV_JWT_SECRET: str = "discourse-dev-secret-change-in-production"

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
