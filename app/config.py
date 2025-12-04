# src/app/config.py

"""
Loads all environment variables from .env using Pydantic BaseSettings.

Supports:
- Gemini API
- Supabase (optional)
- SerpAPI (new)
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # -----------------------------
    # Gemini
    # -----------------------------
    gemini_api_key: str
    gemini_api_url: str

    # -----------------------------
    # Supabase (optional)
    # -----------------------------
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # -----------------------------
    # SerpAPI  (NEW)
    # -----------------------------
    serpapi_key: str                 # must exist in .env
    serpapi_engine: str = "google_news"
    serpapi_region: str = "IN"
    serpapi_language: str = "en"

    class Config:
        env_file = ".env"


settings = Settings()
