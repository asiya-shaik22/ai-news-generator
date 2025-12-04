# app/services/scraper.py
# SerpApi-backed scraper (async, safe)
# Returns list[dict]: {url, title, summary, snippet, raw_html}

import asyncio
import httpx
import os
from urllib.parse import quote, unquote
from app.config import settings  # assume you added serpapi_key etc here

SERPAPI_BASE = "https://serpapi.com/search.json"


class Scraper:
    def __init__(self):
        # prefer settings; fallback to env
        self.api_key = getattr(settings, "serpapi_key", None) or os.getenv("SERPAPI_KEY")
        self.engine = getattr(settings, "serpapi_engine", "google_news")
        self.region = getattr(settings, "serpapi_region", "IN")
        self.language = getattr(settings, "serpapi_language", "en")

        if not self.api_key:
            raise RuntimeError("SERPAPI_KEY is required in environment or settings")

        # Default HTTP timeout
        self._timeout = 20

    async def _call_serpapi(self, query: str, num: int = 5) -> dict:
        """
        Call SerpApi/google_news endpoint and return parsed JSON.
        """
        params = {
            "engine": self.engine,
            "q": query,
            "hl": self.language,
            "gl": self.region,
            "api_key": self.api_key,
            # SerpApi supports a 'num' param for some engines; we'll limit locally
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(SERPAPI_BASE, params=params)
        resp.raise_for_status()
        return resp.json()

    async def search_and_scrape(self, keyword: str) -> list[dict]:
        """
        Main entry used by rest of pipeline.
        Uses SerpApi to fetch news results and returns normalized list:
        [{url, title, summary, snippet, raw_html}]
        """
        try:
            data = await self._call_serpapi(keyword, num=10)
        except Exception as e:
            print("SerpApi error:", type(e), str(e))
            return []

        results = []

        # The google_news engine returns "news_results" (list) in SerpApi responses.
        # See: https://serpapi.com/google-news-api
        news_items = data.get("news_results") or data.get("news") or []

        for item in news_items[:10]:  # cap results
            link = item.get("link") or item.get("source_url") or item.get("url")
            title = item.get("title") or item.get("headline") or ""
            snippet = item.get("snippet") or item.get("snippet_text") or ""
            # Use snippet as summary to avoid fetching the whole page.
            summary = snippet if snippet else item.get("abstract") or ""

            # normalize
            if link:
                link = unquote(link)

            results.append({
                "url": link,
                "title": title,
                "summary": summary,
                "snippet": snippet,
                "raw_html": None  # we are not fetching article HTML here
            })

        return results
