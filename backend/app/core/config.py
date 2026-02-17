"""
EduCore Backend - Core Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App
    APP_NAME: str = "EduCore API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @property
    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from env (handles JSON string)"""
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    # Database (direct connection for some operations)
    DATABASE_URL: Optional[str] = None

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False

    # Celery Configuration
    CELERY_BROKER_URL: Optional[str] = None  # Falls back to REDIS_URL
    CELERY_RESULT_BACKEND: Optional[str] = None  # Falls back to REDIS_URL
    CELERY_TASK_ALWAYS_EAGER: bool = False  # True for testing without Redis

    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL"""
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        """Get Celery result backend URL"""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    # Cache Configuration
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes
    CACHE_DASHBOARD_TTL: int = 60  # 1 minute for dashboard data
    CACHE_USER_TTL: int = 600  # 10 minutes for user data

    # Security Settings
    MFA_ENABLED: bool = True
    MFA_ISSUER: str = "EduSMS"
    SESSION_MAX_AGE_HOURS: int = 24
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20

    # File Storage
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "doc", "docx", "jpg", "jpeg", "png", "gif"]

    # External Services (Phase 3)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[str] = None

    # Google Integration (Phase 3)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Microsoft Integration (Phase 3)
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_TENANT_ID: Optional[str] = None

    # OpenAI (Phase 4)
    OPENAI_API_KEY: Optional[str] = None

    # Firebase (Phase 5)
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
