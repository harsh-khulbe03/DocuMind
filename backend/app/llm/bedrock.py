import json
from collections.abc import AsyncIterator

from tenacity import retry, stop_after_attempt, wait_exponential

from app.llm.base import LLMProvider


class BedrockProvider(LLMProvider):
    def __init__(
        self,
        model_id: str,
        region: str,
        access_key_id: str = "",
        secret_access_key: str = "",
    ) -> None:
        self.model_id = model_id
        self.region = region
        self.access_key_id = access_key_id or None
        self.secret_access_key = secret_access_key or None

    def _client(self):
        import boto3
        return boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        import asyncio

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        })

        def _stream_sync():
            client = self._client()
            response = client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                if chunk.get("type") == "content_block_delta":
                    yield chunk["delta"].get("text", "")

        # Run the synchronous boto3 stream in a thread
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _producer():
            try:
                for token in _stream_sync():
                    loop.call_soon_threadsafe(queue.put_nowait, token)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        loop.run_in_executor(None, _producer)

        while True:
            token = await queue.get()
            if token is None:
                break
            if token:
                yield token

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def complete(self, system: str, user: str) -> str:
        tokens = []
        async for token in self.stream(system, user):
            tokens.append(token)
        return "".join(tokens)
