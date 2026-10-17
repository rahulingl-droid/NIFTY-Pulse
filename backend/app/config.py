"""
Configuration Settings for NIFTY-Pulse Platform.
Supports Azure Cloud deployment, environment variables, and security parameters.
"""
import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


class AppConfig(BaseModel):
    # Application Info
    APP_NAME: str = "NIFTY-Pulse"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Azure Cloud Settings
    AZURE_REGION: str = os.getenv("AZURE_REGION", "centralindia")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    AZURE_SUBSCRIPTION_ID: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    AZURE_KEY_VAULT_NAME: str = os.getenv("AZURE_KEY_VAULT_NAME", "kv-nifty-pulse")
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

    # LLM & AI Provider Settings (Optional Azure OpenAI / Google Gemini)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")

    # Market Refresh Intervals (Seconds)
    MARKET_TICK_INTERVAL_SEC: int = int(os.getenv("MARKET_TICK_INTERVAL_SEC", "3"))
    AGENT_SCAN_INTERVAL_SEC: int = int(os.getenv("AGENT_SCAN_INTERVAL_SEC", "30"))

    # Security & CORS
    CORS_ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",  # Permissive for development/container testing
    ]


config = AppConfig()
