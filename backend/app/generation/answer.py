from collections.abc import AsyncIterator

from app.llm.base import LLMProvider
from app.models import SourceChunk

SYSTEM_PROMPT = """You are DocuMind, a precise document assistant.
Answer the user's question using ONLY the context passages provided.
Rules:
- Cite sources inline as [doc: <filename>, p.<page>].
- If the context does not contain enough information to answer, say exactly:
  "I don't have enough information in the provided documents to answer this question."
- Never invent facts not present in the context.
- Be concise and direct."""


def _build_user_prompt(question: str, sources: list[SourceChunk]) -> str:
    context_blocks = "\n\n".join(
        f"[Source: {s.filename}, page {s.page}]\n{s.text}"
        for s in sources
    )
    return f"Context:\n{context_blocks}\n\nQuestion: {question}"


async def stream_answer(
    question: str,
    sources: list[SourceChunk],
    llm: LLMProvider,
) -> AsyncIterator[str]:
    user_prompt = _build_user_prompt(question, sources)
    async for token in llm.stream(SYSTEM_PROMPT, user_prompt):
        yield token


async def get_answer(
    question: str,
    sources: list[SourceChunk],
    llm: LLMProvider,
) -> str:
    user_prompt = _build_user_prompt(question, sources)
    return await llm.complete(SYSTEM_PROMPT, user_prompt)


INSUFFICIENT_ANSWER = (
    "I don't have enough information in the provided documents to answer this question."
)


def is_insufficient(answer: str) -> bool:
    return INSUFFICIENT_ANSWER.lower() in answer.lower()
