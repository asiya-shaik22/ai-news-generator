from app.services.semantic_engine import SemanticEngine
from app.services.supabase_client import SupabaseClient
from app.services.llm_client import GeminiClient

class IdeaGenerator:
    def __init__(self):
        self.db = SupabaseClient()
        self.gemini = GeminiClient()
        self.semantic = SemanticEngine()

    async def save_article(self, article: dict):
        # avoid duplicate inserts
        exists = await self.db.fetch_one("articles", {"url": article.get("url")})
        if exists:
            return None

        data = {
            "url": article.get("url"),
            "title": (article.get("title") or "")[:500],
            "summary": (article.get("summary") or "")[:2000],
            "snippet": (article.get("snippet") or "")[:300],
        }

        return await self.db.insert("articles", data)

    async def get_all_articles(self):
        return await self.db.fetch_all("articles")

    async def get_recent_articles(self, limit: int = 20):
        query = f"select=*&order=created_at.desc&limit={limit}"
        return await self.db.fetch_all(f"articles?{query}")

    async def generate_ideas(self):
        articles = await self.get_recent_articles(limit=5)
        if not articles:
            return ["No articles found. Please scrape first."]

        context = "\n\n".join(
            f"Title: {a.get('title')}\nSummary: {(a.get('summary') or '')[:1000]}"
            for a in articles
        )

        prompt = (
            "Use the following news summaries to generate 5 fresh short article ideas.\n\n"
            f"{context}"
        )

        ideas_text = await self.gemini.raw_prompt(prompt)
        ideas = [i.strip("•-● ").strip() for i in ideas_text.split("\n") if i.strip()]
        return ideas[:10]

    async def generate_ideas_from_list(self, articles: list[dict]):
        if not articles:
            return ["No relevant articles found for this keyword."]

        context = "\n\n".join(
            f"Title: {a.get('title')}\nSummary: {(a.get('summary') or '')[:1000]}"
            for a in articles
        )

        prompt = (
            "Using the following summaries, generate 5 concise news article ideas:\n\n"
            f"{context}"
        )

        ideas_text = await self.gemini.raw_prompt(prompt)
        ideas = [i.strip("•-● ").strip() for i in ideas_text.split("\n") if i.strip()]
        return ideas[:10]

    async def generate_ideas_by_keyword(self, keyword: str):
        if not keyword:
            return ["Keyword required"]

        all_articles = await self.db.fetch_all("articles")
        if not all_articles:
            return [f"No articles found for '{keyword}'"]

        relevant = self.semantic.find_relevant(keyword, all_articles, top_k=10)
        if not relevant:
            return [f"No relevant articles found for '{keyword}'"]

        return await self.generate_ideas_from_list(relevant)
