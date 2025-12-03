from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.llm_client import GeminiClient
from app.services.idea_generator import IdeaGenerator
from app.services.scraper import Scraper

router = APIRouter(prefix="/api/v1")

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
    saved_articles: int
    ideas: List[str]


# ---------------- 1. Expand keywords ----------------
@router.post("/expand")
async def expand_keywords(payload: ExpandRequest):
    if not payload.keywords:
        raise HTTPException(400, "Keywords cannot be empty")

    gemini = GeminiClient()
    expanded = await gemini.expand_keywords(payload.keywords)
    expanded = expanded[:10]  # cap to prevent overload

    return {"expanded_keywords": expanded}


# ---------------- 2. Scrape only ----------------
@router.post("/scrape", response_model=List[ArticleOut])
async def scrape_data(payload: ScrapeRequest):
    if not payload.keywords:
        raise HTTPException(400, "Keywords cannot be empty")

    scraper = Scraper()
    all_articles = []

    for kw in payload.keywords:
        scraped = await scraper.search_and_scrape(kw)

        cleaned = [
            {
                "url": art["url"],
                "title": art["title"],
                "summary": art["summary"],
                "snippet": art["snippet"],
            }
            for art in scraped if art.get("summary")
        ]

        all_articles.extend(cleaned[:2])  # top 2 cleaned

    return all_articles


# ---------------- 3. Get stored articles ----------------
@router.get("/articles", response_model=List[ArticleOut])
async def get_articles():
    idea = IdeaGenerator()
    return await idea.get_all_articles()


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

    all_cleaned = []
    saved_count = 0

    seed_keyword = payload.keywords[0]

    for kw in expanded:
        scraped = await scraper.search_and_scrape(kw)

        cleaned = [
            {
                "url": art["url"],
                "title": art["title"],
                "summary": art["summary"],
                "snippet": art["snippet"],
            }
            for art in scraped if art.get("summary")
        ]

        cleaned = cleaned[:10]  # consistent limit

        # semantic filtering BEFORE saving
        relevant = idea.semantic.find_relevant(seed_keyword, cleaned, top_k=10)

        all_cleaned.extend(relevant)

        # save only relevant & unique
        for art in relevant[:5]:
            inserted = await idea.save_article(art)
            if inserted:
                saved_count += 1

    if not all_cleaned:
        return CombinedResponse(
            seed_keywords=payload.keywords,
            expanded_keywords=expanded,
            saved_articles=0,
            ideas=["No articles scraped. Try different keywords."]
        )

    ideas = await idea.generate_ideas_from_list(all_cleaned)

    return CombinedResponse(
        seed_keywords=payload.keywords,
        expanded_keywords=expanded,
        saved_articles=saved_count,
        ideas=ideas
    )
