import json
from collections.abc import AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
            "keep_alive": "30m",  # avoid ~24s cold model reload between queries
        }
        # CPU inference is slow: allow a long read timeout for time-to-first-token
        # (cold load + prompt eval), short connect timeout to fail fast if Ollama is down.
        timeout = httpx.Timeout(300.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def complete(self, system: str, user: str) -> str:
        tokens = []
        async for token in self.stream(system, user):
            tokens.append(token)
        return "".join(tokens)
