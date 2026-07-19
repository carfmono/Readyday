from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "ReadyDay API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 30  # 30 días

    # Database
    database_url: str = "sqlite:////app/data/readyday.db"

    # Anthropic (Claude — para explicaciones en lenguaje natural)
    anthropic_api_key: str = ""

    # Garmin (fallback global — por usuario se guarda en DB)
    garmin_email: str = ""
    garmin_password: str = ""

    # Encryption (para credenciales Garmin por usuario)
    encryption_key: str = ""  # genera con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    # Push Notifications (FCM para Android)
    fcm_server_key: str = ""  # Firebase Cloud Messaging legacy key

    # Notificación mañanera
    notification_hour: int = 7   # 7am hora local del servidor
    notification_minute: int = 0

    # CORS
    allowed_origins: list[str] = [
        "http://fergussononline.org",
        "https://fergussononline.org",
        "http://www.fergussononline.org",
        "https://www.fergussononline.org",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
