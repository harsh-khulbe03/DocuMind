from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    @abstractmethod
    def stream(self, system: str, user: str) -> AsyncIterator[str]:
        """Yield text tokens as they arrive (async generator)."""
        ...

    @abstractmethod
    async def complete(self, system: str, user: str) -> str:
        """Return the full completion string."""
        ...
