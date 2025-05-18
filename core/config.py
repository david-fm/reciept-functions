import os
from pydantic_settings import BaseSettings
from models import CategoriesData


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Receipt Tracker"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret-key-for-dev")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 180

    # Stripe Configuration
    DOMAIN: str = os.getenv("DOMAIN", "http://localhost:4242")
    STRIPE_PRICE_ID: str = os.getenv("STRIPE_PRICE_ID", "")
    STRIPE_ENDPOINT_SECRET: str = os.getenv("STRIPE_ENDPOINT_SECRET", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLIC_KEY: str = os.getenv("STRIPE_PUBLIC_KEY", "")

    GOOGLE_CLOUD_REGION: str = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    VERTEXAI_MODEL_NAME: str = os.getenv("VERTEXAI_MODEL_NAME", "text-bison")

    categories_data: CategoriesData | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings object
settings = Settings()
