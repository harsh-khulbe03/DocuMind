import asyncio
import logging
from pathlib import Path

from app.config import Settings
from app.indexing.embedder import Embedder
from app.indexing.lexical_store import LexicalStore
from app.indexing.vector_store import VectorStore
from app.ingestion.chunker import chunk_pages
from app.ingestion.parser import parse_pdf

logger = logging.getLogger(__name__)


async def run_ingestion(
    pdf_path: Path,
    doc_id: str,
    filename: str,
    settings: Settings,
) -> int:
    """
    Full ingestion pipeline. Returns chunk count on success, raises on failure.
    Runs in a background task — does NOT block the HTTP response.
    """
    lexical = LexicalStore(settings)
    vector = VectorStore(settings)
    embedder = Embedder(settings)

    try:
        lexical.set_status(doc_id, "processing")

        # ── 1. Parse ───────────────────────────────────────────────────────────
        logger.info("Parsing %s", filename)
        # Docling is CPU-bound — run in a thread pool so we don't block the loop
        pages = await asyncio.get_event_loop().run_in_executor(
            None, parse_pdf, pdf_path
        )
        logger.info("Parsed %d pages from %s", len(pages), filename)

        # ── 2. Chunk ───────────────────────────────────────────────────────────
        chunks = chunk_pages(pages, doc_id, filename, settings.chunk_max_tokens)
        logger.info("Produced %d chunks from %s", len(chunks), filename)

        if not chunks:
            raise ValueError("PDF produced no extractable text chunks.")

        # ── 3. Embed + index (vector) ──────────────────────────────────────────
        texts = [c.text for c in chunks]
        embeddings = await embedder.embed_batch(texts)

        await vector.upsert(chunks, embeddings)
        logger.info("Upserted %d vectors for %s", len(chunks), doc_id)

        # ── 4. Index (lexical) ─────────────────────────────────────────────────
        lexical.upsert_chunks(chunks)
        logger.info("Indexed %d chunks in FTS5 for %s", len(chunks), doc_id)

        # ── 5. Mark ready ──────────────────────────────────────────────────────
        lexical.set_status(doc_id, "ready", chunk_count=len(chunks))
        return len(chunks)

    except Exception as exc:
        logger.exception("Ingestion failed for %s: %s", doc_id, exc)
        lexical.set_status(doc_id, "failed", error=str(exc))
        raise
