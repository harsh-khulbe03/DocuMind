from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ── Document models ────────────────────────────────────────────────────────────

class DocumentStatus(BaseModel):
    doc_id: str
    filename: str
    status: str          # "processing" | "ready" | "failed"
    chunk_count: int = 0
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentStatus]


class DeleteResponse(BaseModel):
    doc_id: str
    deleted: bool


# ── Ingestion job models ───────────────────────────────────────────────────────

class IngestJobResponse(BaseModel):
    doc_id: str
    filename: str
    status: str = "processing"
    message: str = "Ingestion started"


# ── Query models ───────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    doc_ids: list[str] | None = Field(
        default=None,
        description="Scope query to specific documents. None = all documents.",
    )


class SourceChunk(BaseModel):
    doc_id: str
    filename: str
    page: int
    text: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    confidence: float
    insufficient_coverage: bool = False


# ── Chunk (internal, used across ingestion + indexing) ────────────────────────

class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page: int
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
