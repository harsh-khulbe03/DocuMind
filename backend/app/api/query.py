import asyncio
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.generation.answer import get_answer, is_insufficient, stream_answer
from app.llm.factory import get_llm
from app.models import QueryRequest, QueryResponse, SourceChunk
from app.rate_limit import rate_limiter
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.reranker import rerank
from app.retrieval.vector import VectorRetriever

logger = logging.getLogger(__name__)
router = APIRouter()

_query_limit = rate_limiter(get_settings().query_rate_per_minute, 60, "query")


async def _retrieve_and_rerank(
    request: QueryRequest,
    settings: Settings,
) -> tuple[list[SourceChunk], float]:
    """
    Run vector + lexical retrieval in parallel, fuse, rerank.
    Returns (sources, top_score).
    """
    vector_retriever = VectorRetriever(settings)
    lexical_retriever = LexicalRetriever(settings)

    # Run vector and lexical in parallel
    vector_results, lexical_results = await asyncio.gather(
        vector_retriever.retrieve(request.question, request.doc_ids),
        asyncio.get_event_loop().run_in_executor(
            None,
            lexical_retriever.retrieve,
            request.question,
            request.doc_ids,
        ),
    )

    # Fuse
    fused = reciprocal_rank_fusion(vector_results, lexical_results)

    if not fused:
        return [], 0.0

    # Rerank (CPU-bound — run in executor)
    reranked = await asyncio.get_event_loop().run_in_executor(
        None,
        rerank,
        request.question,
        fused,
        settings.rerank_top_n,
        settings.rerank_model,
    )

    top_score = reranked[0]["score"] if reranked else 0.0

    sources = [
        SourceChunk(
            doc_id=c["doc_id"],
            filename=c["filename"],
            page=c["page"],
            text=c["text"],
            score=c["score"],
        )
        for c in reranked
    ]
    return sources, top_score


@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(_query_limit),
):
    """Non-streaming query endpoint. Returns full answer + sources."""
    sources, top_score = await _retrieve_and_rerank(request, settings)

    # Only short-circuit when retrieval found nothing at all. The cross-encoder
    # score ranks well but isn't a calibrated confidence, so coverage is judged
    # by the grounded LLM (is_insufficient), not a threshold on top_score.
    if not sources:
        return QueryResponse(
            answer="I don't have enough information in the provided documents to answer this question.",
            sources=[],
            confidence=top_score,
            insufficient_coverage=True,
        )

    llm = get_llm(settings)
    answer = await get_answer(request.question, sources, llm)

    return QueryResponse(
        answer=answer,
        sources=sources,
        confidence=top_score,
        insufficient_coverage=is_insufficient(answer),
    )


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(_query_limit),
):
    """
    Streaming query endpoint using Server-Sent Events.
    Emits:
        data: {"type": "source", ...source chunk...}
        data: {"type": "token", "text": "..."}
        data: {"type": "done", "insufficient_coverage": bool}
    """
    sources, top_score = await _retrieve_and_rerank(request, settings)

    async def event_stream():
        # First, send all sources
        for source in sources:
            payload = json.dumps({"type": "source", **source.model_dump()})
            yield f"data: {payload}\n\n"

        if not sources:
            insufficient_msg = (
                "I don't have enough information in the provided documents to answer this question."
            )
            yield f"data: {json.dumps({'type': 'token', 'text': insufficient_msg})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'insufficient_coverage': True})}\n\n"
            return

        llm = get_llm(settings)
        answer_tokens = []
        async for token in stream_answer(request.question, sources, llm):
            answer_tokens.append(token)
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

        full_answer = "".join(answer_tokens)
        yield f"data: {json.dumps({'type': 'done', 'insufficient_coverage': is_insufficient(full_answer)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disables nginx buffering for SSE
        },
    )
