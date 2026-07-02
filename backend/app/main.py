from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import documents, query
from app.config import get_settings
from app.indexing.lexical_store import LexicalStore
from app.indexing.vector_store import VectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise shared resources on startup, clean up on shutdown."""
    settings = get_settings()

    # Ensure Qdrant collection exists
    vs = VectorStore(settings)
    await vs.ensure_collection()

    # Ensure SQLite schema exists
    ls = LexicalStore(settings)
    ls.ensure_schema()

    yield
    # Nothing to explicitly tear down for local use


def create_app() -> FastAPI:
    app = FastAPI(
        title="DocuMind",
        description="Document Q&A with hybrid search and citations.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(documents.router, prefix="/documents", tags=["documents"])
    app.include_router(query.router, prefix="/query", tags=["query"])

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
