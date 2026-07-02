import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import Settings
from app.indexing.embedder import Embedder
from app.models import Chunk

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
        self._embedder = Embedder(settings)

    async def ensure_collection(self) -> None:
        collections = await self.client.get_collections()
        names = [c.name for c in collections.collections]
        if self.settings.qdrant_collection not in names:
            dim = self._embedder.get_dimension()
            await self.client.create_collection(
                collection_name=self.settings.qdrant_collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            logger.info(
                "Created Qdrant collection '%s' (dim=%d)",
                self.settings.qdrant_collection,
                dim,
            )

    async def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        points = [
            PointStruct(
                id=abs(hash(c.chunk_id)) % (2**63),  # Qdrant needs uint64
                vector=emb,
                payload={
                    "chunk_id": c.chunk_id,
                    "doc_id": c.doc_id,
                    "filename": c.filename,
                    "page": c.page,
                    "text": c.text,
                },
            )
            for c, emb in zip(chunks, embeddings)
        ]
        await self.client.upsert(
            collection_name=self.settings.qdrant_collection,
            points=points,
        )

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        doc_ids: list[str] | None = None,
    ) -> list[dict]:
        query_filter = None
        if doc_ids:
            query_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchAny(any=doc_ids))]
            )

        response = await self.client.query_points(
            collection_name=self.settings.qdrant_collection,
            query=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        results = response.points

        return [
            {
                "chunk_id": r.payload["chunk_id"],
                "doc_id": r.payload["doc_id"],
                "filename": r.payload["filename"],
                "page": r.payload["page"],
                "text": r.payload["text"],
                "score": r.score,
            }
            for r in results
            if r.payload
        ]

    async def delete_by_doc_id(self, doc_id: str) -> None:
        await self.client.delete(
            collection_name=self.settings.qdrant_collection,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
        )
        logger.info("Deleted vectors for doc_id=%s", doc_id)
