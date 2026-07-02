import logging
import sqlite3
from datetime import datetime, timezone

from app.config import Settings
from app.models import Chunk, DocumentStatus

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LexicalStore:
    def __init__(self, settings: Settings) -> None:
        self.db_path = settings.sqlite_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def ensure_schema(self) -> None:
        with self._conn() as conn:
            # Document metadata + status tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id      TEXT PRIMARY KEY,
                    filename    TEXT NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'processing',
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    error       TEXT,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                )
            """)
            # FTS5 virtual table — BM25 ranking built in
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_id,
                    doc_id     UNINDEXED,
                    filename   UNINDEXED,
                    page       UNINDEXED,
                    text,
                    tokenize = 'porter ascii'
                )
            """)
            conn.commit()

    # ── Document status ────────────────────────────────────────────────────────

    def create_document(self, doc_id: str, filename: str) -> None:
        now = _now()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO documents (doc_id, filename, status, created_at, updated_at)
                VALUES (?, ?, 'processing', ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    filename=excluded.filename,
                    status='processing',
                    error=NULL,
                    updated_at=excluded.updated_at
                """,
                (doc_id, filename, now, now),
            )
            conn.commit()

    def set_status(
        self,
        doc_id: str,
        status: str,
        chunk_count: int = 0,
        error: str | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE documents
                SET status=?, chunk_count=?, error=?, updated_at=?
                WHERE doc_id=?
                """,
                (status, chunk_count, error, _now(), doc_id),
            )
            conn.commit()

    def get_document(self, doc_id: str) -> DocumentStatus | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
            ).fetchone()
        if not row:
            return None
        return DocumentStatus(**dict(row))

    def list_documents(self) -> list[DocumentStatus]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
        return [DocumentStatus(**dict(r)) for r in rows]

    def delete_document(self, doc_id: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM chunks_fts WHERE doc_id = ?", (doc_id,))
            conn.commit()
        return cur.rowcount > 0

    # ── Chunks FTS ─────────────────────────────────────────────────────────────

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        with self._conn() as conn:
            # Remove old entries for this doc first (idempotent re-ingest)
            if chunks:
                conn.execute("DELETE FROM chunks_fts WHERE doc_id = ?", (chunks[0].doc_id,))
            conn.executemany(
                "INSERT INTO chunks_fts (chunk_id, doc_id, filename, page, text) VALUES (?,?,?,?,?)",
                [(c.chunk_id, c.doc_id, c.filename, c.page, c.text) for c in chunks],
            )
            conn.commit()

    def search(
        self,
        query: str,
        top_k: int,
        doc_ids: list[str] | None = None,
    ) -> list[dict]:
        # FTS5 bm25() returns negative scores — more negative = better match
        if doc_ids:
            placeholders = ",".join("?" * len(doc_ids))
            sql = f"""
                SELECT chunk_id, doc_id, filename, page, text,
                       bm25(chunks_fts) AS score
                FROM chunks_fts
                WHERE chunks_fts MATCH ?
                  AND doc_id IN ({placeholders})
                ORDER BY score
                LIMIT ?
            """
            params = [query, *doc_ids, top_k]
        else:
            sql = """
                SELECT chunk_id, doc_id, filename, page, text,
                       bm25(chunks_fts) AS score
                FROM chunks_fts
                WHERE chunks_fts MATCH ?
                ORDER BY score
                LIMIT ?
            """
            params = [query, top_k]

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            {
                "chunk_id": r["chunk_id"],
                "doc_id": r["doc_id"],
                "filename": r["filename"],
                "page": r["page"],
                "text": r["text"],
                "score": abs(r["score"]),  # normalise to positive (higher = better)
            }
            for r in rows
        ]
