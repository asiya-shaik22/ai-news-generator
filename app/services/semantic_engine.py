# app/services/semantic_engine.py

from sentence_transformers import SentenceTransformer, util


class SemanticEngine:
    def __init__(self):
        # Lightweight & fast semantic similarity model
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def find_relevant(self, keyword: str, articles: list[dict], top_k: int = 5):
        """
        Pure semantic TOP-K ranking.
        No thresholds. No keyword hacks.
        Works for ANY topic including cyclone breaking news.
        """

        if not articles:
            return []

        # Combine title + summary for embeddings
        docs = [
            f"{a.get('title', '')} {a.get('summary', '')}".strip()
            for a in articles
        ]

        try:
            kw_emb = self.model.encode(keyword, convert_to_tensor=True)
            doc_emb = self.model.encode(docs, convert_to_tensor=True)
        except Exception as e:
            print("Embedding error:", e)
            return articles[:top_k]

        # Compute similarity
        scores = util.cos_sim(kw_emb, doc_emb)[0]

        # Rank docs by score
        ranked = list(zip(articles, scores))
        ranked.sort(key=lambda x: float(x[1]), reverse=True)

        # Return TOP-K relevant articles
        return [a for a, _ in ranked[:top_k]]
