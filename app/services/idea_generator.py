
from app.services.supabase_client import SupabaseClient
from app.services.llm_client import GeminiClient


class IdeaGenerator:
    def __init__(self):
        self.db = SupabaseClient()
        self.gemini = GeminiClient()

    # ----------------------------------------------------
    # SAVE ARTICLE (with safe text limits)
    # ----------------------------------------------------
    async def save_article(self, article: dict):

        title = (article.get("title") or "")[:500]
        summary = (article.get("summary") or "")[:2000]   # reduced for speed
        snippet = (article.get("snippet") or "")[:300]

        data = {
            "url": article.get("url"),
            "title": title,
            "summary": summary,
            "snippet": snippet,
            "raw_html": (article.get("raw_html") or "")[:20000],  # trim HTML
        }

        return await self.db.insert("articles", data)
    
    
    # ----------------------------------------------------
    # FETCH ALL ARTICLES (for /articles endpoint)
    # ----------------------------------------------------
    async def get_all_articles(self):
        return await self.db.fetch_all("articles")


    # ----------------------------------------------------
    # FETCH ONLY LATEST 20 ARTICLES (super fast)
    # ----------------------------------------------------
    async def get_recent_articles(self, limit: int = 20):
        """
        Load only the most recent articles instead of entire DB.
        Speeds up the LLM prompt significantly.
        """

        query = f"select=*&order=created_at.desc&limit={limit}"
        return await self.db.fetch_all(f"articles?{query}")

    # ----------------------------------------------------
    # GENERATE IDEAS FROM ARTICLES
    # ----------------------------------------------------
    async def generate_ideas(self):

        # 1) Fetch only latest 20 articles
        articles = await self.get_recent_articles(limit=20)

        if not articles:
            return ["No articles found. Please scrape first."]

        # 2) Build trimmed context
        context_parts = []
        for a in articles:
            title = (a.get("title") or "").strip()
            summary = (a.get("summary") or "").strip()

            # reduce per-article summary size
            summary = summary[:400]

            context_parts.append(f"Title: {title}\nSummary: {summary}")

        context = "\n\n".join(context_parts)

        # 3) Final prompt
        prompt = (
            "Use the following news article summaries to generate 5 fresh, "
            "unique, trending news article ideas.\n"
            "Keep ideas short, clear, and interesting.\n\n"
            f"{context}"
        )

        # 4) Send to Gemini
        ideas_text = await self.gemini.raw_prompt(prompt)

        # 5) Clean and convert to list
        ideas = [
            i.strip("•-● ").strip()
            for i in ideas_text.split("\n")
            if i.strip()
        ]

        return ideas[:10]   # return top 10 ideas
