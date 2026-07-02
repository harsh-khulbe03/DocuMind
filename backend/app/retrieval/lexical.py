from app.config import Settings
from app.indexing.lexical_store import LexicalStore


class LexicalRetriever:
    def __init__(self, settings: Settings) -> None:
        self.lexical_store = LexicalStore(settings)
        self.top_k = settings.lexical_top_k

    def retrieve(self, query: str, doc_ids: list[str] | None = None) -> list[dict]:
        # Sanitise query for FTS5: wrap in quotes to treat as phrase,
        # fall back to individual terms if no results.
        try:
            results = self.lexical_store.search(f'"{query}"', self.top_k, doc_ids)
        except Exception:
            results = []

        if not results:
            # Strip special chars and retry as individual terms
            safe_query = " ".join(
                word for word in query.split() if word.isalnum() or len(word) > 2
            )
            if safe_query:
                try:
                    results = self.lexical_store.search(safe_query, self.top_k, doc_ids)
                except Exception:
                    results = []

        return results
