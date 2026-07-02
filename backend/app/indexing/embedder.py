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
}


class Embedder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.settings.llm_provider == "ollama":
            return await self._embed_ollama(texts)
        return await self._embed_bedrock(texts)

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
        if self.settings.llm_provider == "ollama":
            model = self.settings.ollama_embedding_model
        else:
            model = self.settings.bedrock_embedding_model_id
        return EMBEDDING_DIMS.get(model, 768)
