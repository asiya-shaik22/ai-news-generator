# app/services/llm_client.py

"""
GeminiClient
------------
Handles all LLM interactions:
1. expand_keywords() → returns exactly 10 SEO keywords
2. raw_prompt() → generic LLM prompt
"""

import httpx
from app.config import settings


class GeminiClient:
    """Async client for Google Gemini API."""

    def __init__(self):
        self.api_url = settings.gemini_api_url
        self.api_key = settings.gemini_api_key
        self.model = "gemini-2.5-flash"

    # ------------------------------------------------------------
    # 1. Expand Keywords
    # ------------------------------------------------------------
    async def expand_keywords(self, user_keywords: list[str]) -> list[str]:

        prompt = (
            "Expand the following into exactly 10 SEO-optimized keywords.\n"
            "Return ONLY the list, separated by commas. No numbering.\n\n"
            f"User keywords: {user_keywords}"
        )

        url = f"{self.api_url}/{self.model}:generateContent?key={self.api_key}"

        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=body)

        response.raise_for_status()
        raw = response.json()

        # --------------------------------------------------------
        # Safe extraction (Gemini sometimes changes response shape)
        # --------------------------------------------------------
        try:
            text = raw["candidates"][0]["content"]["parts"][0]["text"]
        except:
            # fallback for alternate response format
            text = raw["candidates"][0]["content"]["parts"][0].get("raw_text", "")

        # Normalization: handle newlines / bullets / hyphens / pipes
        text = text.replace("\n", ",").replace("•", ",").replace("-", ",").replace("|", ",")

        # Split, strip, drop empty
        expanded = [kw.strip() for kw in text.split(",") if kw.strip()]

        # Guarantee exactly 10 keywords
        if len(expanded) >= 10:
            return expanded[:10]

        # If Gemini returns fewer than 10 → regenerate
        # (simple safe fallback: repeat keywords)
        while len(expanded) < 10:
            expanded.append(expanded[-1])

        return expanded[:10]

    # ------------------------------------------------------------
    # 2. Raw Prompt (Idea generator)
    # ------------------------------------------------------------
    async def raw_prompt(self, prompt: str) -> str:

        url = f"{self.api_url}/{self.model}:generateContent?key={self.api_key}"

        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=body)

        response.raise_for_status()
        raw = response.json()

        # Safe extraction for Gemini shapes
        try:
            return raw["candidates"][0]["content"]["parts"][0]["text"]
        except:
            return raw["candidates"][0]["content"]["parts"][0].get("raw_text", "")
