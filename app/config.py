# src/app/config.py

"""
WHAT?
-----
This file loads all environment variables from your .env file.
We use Pydantic BaseSettings for safe, typed config management.

WHY?
----
Every service (LLM, DB, Scraper) needs config values:
- DATABASE_URL
- GEMINI_API_KEY
- SUPABASE_URL (optional)
- SUPABASE_KEY (optional)

HOW?
----
When the app starts, Settings() automatically reads the .env file.
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Gemini
    gemini_api_key: str
    gemini_api_url: str

    # Supabase (optional)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
