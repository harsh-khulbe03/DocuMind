import logging
from typing import TYPE_CHECKING

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

EMBEDDING_DIMS = {
    # Ollama
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    # Bedrock
    "amazon.titan-embed-text-v2:0": 1024,
    # Local sentence-transformers
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "BAAI/bge-small-en-v1.5": 384,
}

# Cached across requests — loading the model is expensive.
_local_model = None


class Embedder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.settings.embedding_provider == "local":
            return await self._embed_local(texts)
        if self.settings.embedding_provider == "ollama":
            return await self._embed_ollama(texts)
        return await self._embed_bedrock(texts)

    async def _embed_local(self, texts: list[str]) -> list[list[float]]:
        import asyncio

        def _run() -> list[list[float]]:
            global _local_model
            if _local_model is None:
                from sentence_transformers import SentenceTransformer
                _local_model = SentenceTransformer(self.settings.local_embedding_model)
            return _local_model.encode(texts, normalize_embeddings=True).tolist()

        return await asyncio.get_event_loop().run_in_executor(None, _run)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _embed_ollama(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                resp = await client.post(
                    f"{self.settings.ollama_base_url}/api/embeddings",
                    json={"model": self.settings.ollama_embedding_model, "prompt": text},
                )
                resp.raise_for_status()
                embeddings.append(resp.json()["embedding"])
        return embeddings

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _embed_bedrock(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        import boto3
        import json

        client = boto3.client(
            "bedrock-runtime",
            region_name=self.settings.aws_region,
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
        )

        def _embed_one(text: str) -> list[float]:
            body = json.dumps({"inputText": text, "dimensions": 1024, "normalize": True})
            resp = client.invoke_model(
                modelId=self.settings.bedrock_embedding_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            return json.loads(resp["body"].read())["embedding"]

        loop = asyncio.get_event_loop()
        return await asyncio.gather(*[loop.run_in_executor(None, _embed_one, t) for t in texts])

    def get_dimension(self) -> int:
        if self.settings.embedding_provider == "local":
            model = self.settings.local_embedding_model
        elif self.settings.embedding_provider == "ollama":
            model = self.settings.ollama_embedding_model
        else:
            model = self.settings.bedrock_embedding_model_id
        return EMBEDDING_DIMS.get(model, 768)
