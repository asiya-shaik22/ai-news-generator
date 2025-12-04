# app/services/idea_generator.py

from app.services.semantic_engine import SemanticEngine
from app.services.supabase_client import SupabaseClient
from app.services.llm_client import GeminiClient


class IdeaGenerator:
    def __init__(self):
        self.db = SupabaseClient()
        self.gemini = GeminiClient()
        self.semantic = SemanticEngine()

    # --------------------------------------------------
    # SAVE ARTICLE
    # --------------------------------------------------
    async def save_article(self, article: dict):
        title = (article.get("title") or "")[:500]
        summary = (article.get("summary") or "")[:4000]
        snippet = (article.get("snippet") or "")[:300]

        data = {
            "url": article.get("url"),
            "title": title,
            "summary": summary,
            "snippet": snippet
        }

        return await self.db.insert("articles", data)

    # --------------------------------------------------
    # FETCH ALL / RECENT
    # --------------------------------------------------
    async def get_all_articles(self):
        return await self.db.fetch_all("articles")

    async def get_recent_articles(self, limit: int = 20):
        query = f"select=*&order=created_at.desc&limit={limit}"
        return await self.db.fetch_all(f"articles?{query}")

    # --------------------------------------------------
    # CLEANUP CONTEXT BUILDER
    # --------------------------------------------------
    def build_context(self, articles: list[dict]) -> str:
        context_parts = []
        for a in articles:
            title = (a.get("title") or "").strip()
            summary = (a.get("summary") or "").strip()
            if summary:
                summary = summary[:600]
            context_parts.append(f"Title: {title}\nSummary: {summary}")

        return "\n\n".join(context_parts)

    # --------------------------------------------------
    # GENERATE IDEAS FROM RECENT ARTICLES
    # --------------------------------------------------
    async def generate_ideas(self):
        articles = await self.get_recent_articles(limit=5)
        if not articles:
            return ["No articles found. Please scrape first."]

        context = self.build_context(articles)

        prompt = (
            "You are an expert news analyst. Based ONLY on the following real news article summaries, "
            "generate 5 clear, concise, highly relevant news story ideas.\n\n"
            f"{context}\n\n"
            "Ensure all ideas are directly related to the content. Keep them short, crisp, and real."
        )

        ideas_text = await self.gemini.raw_prompt(prompt)
        ideas = [i.strip("•-● ").strip() for i in ideas_text.split("\n") if i.strip()]

        return ideas[:10]

    # --------------------------------------------------
    # GENERATE FROM PROVIDED ARTICLE LIST
    # --------------------------------------------------
    async def generate_ideas_from_list(self, articles: list[dict]):
        if not articles:
            return ["No relevant articles found for this keyword."]

        context = self.build_context(articles)

        prompt = (
            "Based strictly on the following article summaries, produce 5 short and relevant news story ideas. "
            "Do NOT add unrelated topics.\n\n"
            f"{context}"
        )

        ideas_text = await self.gemini.raw_prompt(prompt)
        ideas = [i.strip("•-● ").strip() for i in ideas_text.split("\n") if i.strip()]
        return ideas[:10]

    # --------------------------------------------------
    # GENERATE IDEAS BY KEYWORD (Semantic Filter)
    # --------------------------------------------------
    async def generate_ideas_by_keyword(self, keyword: str):
        if not keyword:
            return ["Keyword required"]

        all_articles = await self.db.fetch_all("articles")
        if not all_articles:
            return [f"No articles found in DB for '{keyword}'"]

        # Semantic TOP-K relevance detection
        relevant = self.semantic.find_relevant(keyword, all_articles, top_k=8)

        if not relevant:
            return [f"No relevant articles found for '{keyword}'"]

        return await self.generate_ideas_from_list(relevant)
