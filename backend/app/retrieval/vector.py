from app.config import Settings
from app.indexing.embedder import Embedder
from app.indexing.vector_store import VectorStore


class VectorRetriever:
    def __init__(self, settings: Settings) -> None:
        self.vector_store = VectorStore(settings)
        self.embedder = Embedder(settings)
        self.top_k = settings.vector_top_k

    async def retrieve(self, query: str, doc_ids: list[str] | None = None) -> list[dict]:
        [embedding] = await self.embedder.embed_batch([query])
        return await self.vector_store.search(embedding, self.top_k, doc_ids)
