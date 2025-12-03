from sentence_transformers import SentenceTransformer, util

class SemanticEngine:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def find_relevant(self, keyword: str, articles: list[dict], top_k: int = 5):
        if not articles:
            return []

        docs = [
            (a.get("title") or "") + " " + (a.get("summary") or "")
            for a in articles
        ]

        doc_embeddings = self.model.encode(docs, convert_to_tensor=True)
        kw_embedding = self.model.encode(keyword, convert_to_tensor=True)

        scores = util.cos_sim(kw_embedding, doc_embeddings)[0]

        scored = list(zip(articles, scores))
        scored.sort(key=lambda x: float(x[1]), reverse=True)

        threshold = 0.36
        relevant = [a for a, s in scored if float(s) >= threshold][:top_k]
        return relevant
