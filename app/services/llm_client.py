# app/services/llm_client.py

"""
This file contains the GeminiClient class.
It communicates with Google Gemini API and provides two features:
1. expand_keywords() → expands user keywords into SEO keywords
2. raw_prompt() → run any custom LLM prompt

We keep this logic separate from main.py and endpoints for clean architecture.
"""

import httpx
from app.config import settings


class GeminiClient:
    """Simple async client for Google Gemini API."""

    def __init__(self):
        # Load from .env through app.config.settings
        self.api_url = settings.gemini_api_url
        self.api_key = settings.gemini_api_key
        self.model = "gemini-2.5-flash"


    async def expand_keywords(self, user_keywords: list[str]) -> list[str]:
        """
        Takes a list of user-provided keywords and asks Gemini to expand them
        into 10 SEO-optimized keywords.
        """

        prompt = (
            "Expand the following keywords into exactly 10 SEO-optimized keywords. "
            "Return only a comma-separated list.\n\n"
            f"User keywords: {user_keywords}"
        )

        # Example:
        # https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=API_KEY
        url = f"{self.api_url}/{self.model}:generateContent?key={self.api_key}"

        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=body)

        response.raise_for_status()

        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

        # Convert "a, b, c" → ["a", "b", "c"]
        expanded = [kw.strip() for kw in text.split(",")]

        return expanded[:10]

    async def raw_prompt(self, prompt: str) -> str:
        """
        Allows sending any direct prompt to Gemini and returns raw text.
        Used for news idea generator.
        """

        url = f"{self.api_url}/{self.model}:generateContent?key={self.api_key}"

        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=body)

        response.raise_for_status()

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
