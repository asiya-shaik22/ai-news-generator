from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_client import GeminiClient
from app.services.idea_generator import IdeaGenerator
from app.services.scraper import Scraper
from typing import Optional

router = APIRouter(prefix="/api/v1")


# -------------------------
# Request Models
# -------------------------
class ExpandRequest(BaseModel):
    keywords: list[str]


class ScrapeRequest(BaseModel):
    keywords: list[str]


# -------------------------
# Response Models
# -------------------------

class ArticleOut(BaseModel):
    url: str
    title: Optional[str]
    summary: Optional[str]
    snippet: Optional[str]


class CombinedResponse(BaseModel):
    seed_keywords: list[str]
    expanded_keywords: list[str]
    saved_articles: int
    ideas: list[str]



# -------------------------
# 1. Expand keywords
# -------------------------
@router.post("/expand")
async def expand_keywords(payload: ExpandRequest):
    if not payload.keywords:
        raise HTTPException(400, "Keywords cannot be empty")

    gemini = GeminiClient()
    expanded = await gemini.expand_keywords(payload.keywords)
    return {"expanded_keywords": expanded}


# -------------------------
# 2. SCRAPE ONLY (NO ideas)
# -------------------------
@router.post("/scrape", response_model=list[ArticleOut])
async def scrape_data(payload: ScrapeRequest):
    if not payload.keywords:
        raise HTTPException(400, "Keywords cannot be empty")

    scraper = Scraper()

    all_articles = []

    for kw in payload.keywords:
        scraped = await scraper.search_and_scrape(kw)

        # CLEAN OUTPUT (no raw_html)
        cleaned = [
            {
                "url": art["url"],
                "title": art["title"],
                "summary": art["summary"],
                "snippet": art["snippet"],
            }
            for art in scraped
        ]

        all_articles.extend(cleaned)

    return all_articles


# -------------------------
# 3. Get stored articles
# -------------------------
@router.get("/articles", response_model=list[ArticleOut])
async def get_articles():
    idea = IdeaGenerator()
    return await idea.get_all_articles()


# -------------------------
# 4. Generate ideas from saved articles
# -------------------------
@router.get("/ideas", response_model=list[str])
async def generate_ideas():
    idea = IdeaGenerator()
    return await idea.generate_ideas()


# -------------------------
# 5. FULL PIPELINE:
#    expand → scrape → store → generate ideas
# -------------------------
@router.post("/scrape-and-generate", response_model=CombinedResponse)
async def scrape_and_generate(payload: ScrapeRequest):
    if not payload.keywords:
        raise HTTPException(400, "Keywords cannot be empty")

    gemini = GeminiClient()
    scraper = Scraper()
    idea = IdeaGenerator()

    # 1) Expand keywords
    expanded = await gemini.expand_keywords(payload.keywords)

    all_articles = []

    # 2) Scrape using expanded keywords
    for kw in expanded:
        scraped = await scraper.search_and_scrape(kw)

        # Save cleaned output for response
        cleaned = [
            {
                "url": art["url"],
                "title": art["title"],
                "summary": art["summary"],
                "snippet": art["snippet"],
            }
            for art in scraped
        ]
        all_articles.extend(cleaned)

        # Save raw data to Supabase
        for art in scraped:
            await idea.save_article(art)

    # 3) Generate fresh article ideas
    ideas = await idea.generate_ideas()

    return {
        "seed_keywords": payload.keywords,
        "expanded_keywords": expanded,
        "saved_articles": len(all_articles),
        "ideas": ideas
    }
