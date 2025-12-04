from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.llm_client import GeminiClient
from app.services.idea_generator import IdeaGenerator
from app.services.scraper import Scraper

router = APIRouter(prefix="/api/v1")


# ---------------- Models ----------------
class ExpandRequest(BaseModel):
    keywords: List[str]


class ScrapeRequest(BaseModel):
    keywords: List[str]


class ArticleOut(BaseModel):
    url: str
    title: Optional[str]
    summary: Optional[str]
    snippet: Optional[str]


class CombinedResponse(BaseModel):
    seed_keywords: List[str]
    expanded_keywords: List[str]
    ideas: List[str]


# ---------------- Helpers / Defaults ----------------
# Global caps to avoid DB bloat and API overuse
MAX_SAVE_PER_RUN = 10   # total articles to save per pipeline run (change to 5 if you prefer)
FULL_FETCH_TOP = 3      # number of top articles to fetch full HTML for richer summary


# ---------------- 1. Expand keywords ----------------
@router.post("/expand")
async def expand_keywords(payload: ExpandRequest):
    if not payload.keywords:
        raise HTTPException(400, "Keywords cannot be empty")

    gemini = GeminiClient()
    expanded = await gemini.expand_keywords(payload.keywords)
    return {"expanded_keywords": expanded[:10]}


# ---------------- 2. Scrape only ----------------
@router.post("/scrape", response_model=List[ArticleOut])
async def scrape_data(payload: ScrapeRequest):
    """
    Scrape and return articles (doesn't save). Uses the Scraper service.
    This endpoint returns up to 5 article objects per keyword (adjustable).
    """
    if not payload.keywords:
        raise HTTPException(400, "Keywords cannot be empty")

    scraper = Scraper()
    all_articles = []

    for kw in payload.keywords:
        scraped = await scraper.search_and_scrape(kw)

        # Prefer snippet from SerpAPI (if using SerpAPI). Accept fallback text.
        cleaned = [
            {
                "url": art.get("url"),
                "title": art.get("title") or "Untitled",
                "summary": art.get("summary") or art.get("snippet") or "Short summary not available.",
                "snippet": art.get("snippet") or "",
            }
            for art in scraped if art.get("url")
        ]

        # keep a few per keyword for preview
        all_articles.extend(cleaned[:5])

    return all_articles


# ---------------- 3. Get stored articles ----------------
@router.get("/articles", response_model=List[ArticleOut])
async def get_articles(limit: int = 10):
    """
    Return recent saved articles. Default limit is 10 (adjustable via query param).
    This ensures Swagger shows recent meaningful rows.
    """
    idea = IdeaGenerator()
    return await idea.get_recent_articles(limit=limit)


# ---------------- 4. Generate ideas ----------------
@router.get("/ideas", response_model=List[str])
async def generate_ideas(keyword: str = None):
    idea = IdeaGenerator()
    if keyword:
        return await idea.generate_ideas_by_keyword(keyword)
    return await idea.generate_ideas()


# ---------------- 5. Scrape & Generate pipeline ----------------
@router.post("/scrape-and-generate", response_model=CombinedResponse)
async def scrape_and_generate(payload: ScrapeRequest):

    if not payload.keywords:
        raise HTTPException(400, "Keywords cannot be empty")

    gemini = GeminiClient()
    scraper = Scraper()
    idea = IdeaGenerator()

    expanded = await gemini.expand_keywords(payload.keywords)
    expanded = expanded[:10]

    seed = payload.keywords[0]

    saved_urls = set()
    saved_articles_list = []   # used only for idea generation

    # SIMPLE FIX: scrape + save max 10
    for kw in expanded:

        if len(saved_urls) >= MAX_SAVE_PER_RUN:
            break

        scraped = await scraper.search_and_scrape(kw)

        for art in scraped:

            if len(saved_urls) >= 10:
                break

            url = art.get("url")
            if not url or url in saved_urls:
                continue

            # insert directly (no summary checks, no semantic checks)
            inserted = await idea.save_article(art)

            
            # print("DEBUG INSERT RESPONSE:", inserted, "TYPE:", type(inserted))

            # If duplicate (409 case) → skip
            if isinstance(inserted, dict) and inserted.get("status") == "duplicate":
                continue

            # If inserted new row → list
            if isinstance(inserted, list):
                saved_urls.add(url)
                saved_articles_list.append(art)

                # print("SAVED COUNT:", len(saved_urls))



    # No articles scraped
    if not saved_articles_list:
        return CombinedResponse(
            seed_keywords=payload.keywords,
            expanded_keywords=expanded,
            ideas=["No articles scraped. Try different keywords."]
        )

    # Generate ideas
    ideas = await idea.generate_ideas_from_list(saved_articles_list)

    return CombinedResponse(
        seed_keywords=payload.keywords,
        expanded_keywords=expanded,
        ideas=ideas
    )
