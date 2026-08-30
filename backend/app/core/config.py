import os
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure .env is explicitly loaded from both root workspace and backend directories
root_workspace = Path(__file__).resolve().parent.parent.parent.parent
root_env = root_workspace / ".env"
backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env, override=True)
if backend_env.exists():
    load_dotenv(dotenv_path=backend_env, override=True)
load_dotenv(override=False)

# Absolute path to root SQLite database
default_db_path = (root_workspace / "razorrecover.db").as_posix()


class Settings(BaseSettings):
    PROJECT_NAME: str = "RazorRecover AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database: Always use absolute database path so backend and scripts share exact same DB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{default_db_path}"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "https://razorrecover.vercel.app",
    ]

    # Google Gemini & LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", os.getenv("LLM_API_KEY", "")))
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Optional OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Razorpay Test Mode
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_demo12345")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "demo_secret_key_67890")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "demo_webhook_secret_abc")

    # Recovery Engine Thresholds
    MAX_AUTONOMOUS_AMOUNT: float = 25000.0  # Actions > ₹25k require human approval
    MAX_AUTONOMOUS_RETRIES: int = 2
    MAX_AUTONOMOUS_DISCOUNT_PERCENT: float = 10.0
    RISK_SCORE_THRESHOLD: float = 0.65

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
