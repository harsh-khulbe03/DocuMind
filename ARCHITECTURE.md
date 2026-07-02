# DocuMind — Architecture and Technology Overview

## What we built

DocuMind is a document question-answering application. A user uploads PDFs and asks
questions in natural language; the system returns concise, source-grounded answers with
inline citations to the exact passages used. It does not answer from the model's general
knowledge: if the uploaded documents do not contain the answer, it says so rather than
fabricating.

The core technique is **retrieval-augmented generation (RAG) with hybrid retrieval**:

1. Each PDF is parsed, split into chunks, embedded into vectors, and indexed twice — once
   in a vector store (semantic search) and once in a keyword index (BM25 lexical search).
2. A question runs through both searches in parallel; the two result lists are merged with
   Reciprocal Rank Fusion, then re-ordered by a cross-encoder reranker.
3. The top passages are passed to a language model, which writes the answer and cites its
   sources, or declines when coverage is insufficient.

## Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend framework | Python 3.12, FastAPI, Uvicorn | HTTP API, async request handling, SSE streaming |
| PDF parsing | Docling | Extracts text and structure from PDFs |
| Chunking | LangChain `RecursiveCharacterTextSplitter` | Splits page text into overlapping chunks |
| Vector database | Qdrant | Stores embeddings; semantic (cosine) search |
| Lexical index | SQLite FTS5 (BM25) | Keyword search and document metadata |
| Embeddings | sentence-transformers / Ollama / Bedrock | Turns text into vectors |
| Reranker | sentence-transformers cross-encoder (`ms-marco-MiniLM-L-6-v2`) | Re-scores fused candidates for relevance |
| LLM | Ollama / Groq / AWS Bedrock | Generates the grounded answer |
| Frontend | React 18, Vite, TypeScript, TailwindCSS | Upload UI, chat, source citations |
| Packaging | Docker, Docker Compose, uv | Reproducible builds and local orchestration |

## Third-party and external services

| Service | Role | Used in |
|---|---|---|
| **Groq** | Free hosted LLM API (OpenAI-compatible), used for chat generation | Production |
| **Qdrant Cloud** | Managed vector database (free 1 GB cluster) | Production |
| **Hugging Face Spaces** | Free Docker hosting for the backend container | Production |
| **Vercel** | Free static hosting for the frontend | Production |
| **Hugging Face Hub** | Downloads the embedding and reranker model weights at runtime | Both |
| **Ollama** | Local LLM and embedding server on the developer machine | Local only |
| **AWS Bedrock** | Optional managed LLM and embeddings (paid) | Optional, either environment |

The LLM provider and the embedding provider are configured **independently**
(`LLM_PROVIDER` and `EMBEDDING_PROVIDER`), so, for example, production uses Groq for chat
and local sentence-transformers for embeddings.

## Local vs production

The same codebase runs in both environments; only environment variables differ.

| Concern | Local development | Production (free tier) |
|---|---|---|
| Orchestration | Docker Compose (backend, frontend, Qdrant containers) | Split across managed services |
| LLM (chat) | Ollama `llama3.2` on the host | Groq `llama-3.3-70b-versatile` |
| Embeddings | Ollama `nomic-embed-text` (768-dim) | Local sentence-transformers `all-MiniLM-L6-v2` (384-dim) |
| Vector store | Qdrant container (`http://qdrant:6333`) | Qdrant Cloud (`https://…:6333` + API key) |
| Lexical store | SQLite file (Docker volume, persistent) | SQLite file (ephemeral on HF Spaces) |
| Frontend | Vite dev server, `localhost:5173` | Static build on Vercel |
| Backend port | 8000 (with hot reload) | 7860 (HF Spaces convention) |
| Reranker | sentence-transformers cross-encoder | Same |

Key configuration variables: `LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `GROQ_API_KEY`,
`QDRANT_URL`, `QDRANT_API_KEY`, `CORS_ORIGINS`. Defaults target local Ollama, so
`docker compose up` works with no cloud accounts.

## Data flow

```
Ingestion:  PDF → Docling parse → chunk → embed ─┬─→ Qdrant (vectors)
                                                 └─→ SQLite FTS5 (lexical)

Query:      question ─┬─→ vector search (top 20) ─┐
                      └─→ lexical search (top 20) ─┴─→ Reciprocal Rank Fusion
                            → cross-encoder rerank (top 5)
                            → grounded LLM answer (streamed via SSE), with citations
```

## Abuse protection

Because the production instance is publicly reachable, the backend enforces limits:
file size (10 MB), total document count (50), and per-IP rate limits on uploads
(20/hour) and queries (30/minute), plus a question-length cap. All are configurable via
environment variables. The limiter is in-memory and per-process, which suits the
single-replica free deployment.

## Known limitations

- **Ephemeral backend storage on Hugging Face Spaces.** The SQLite document list and
  lexical index reset when the Space restarts; Qdrant Cloud vectors persist. Durable state
  would require paid persistent storage or moving metadata to a hosted database.
- **CPU inference.** The free backend has no GPU, so embedding and reranking are slower
  than on accelerated hardware.
- **Scanned/image-only PDFs.** OCR is disabled by default, so PDFs without a text layer
  produce no chunks.

---

## Review

**Sanity Check.** The stack, services, and environment split described here match the
deployed system: Groq for chat, Qdrant Cloud for vectors, sentence-transformers for
embeddings and reranking, backend on Hugging Face Spaces, frontend on Vercel. Local
defaults remain Ollama-based. The independence of `LLM_PROVIDER` and `EMBEDDING_PROVIDER`
is stated because it is easy to misread as a single switch.

**Editorial Check.** British spelling throughout. Tables separate stack, third-party
services, and environment differences to avoid conflation. Limitations are stated plainly
rather than omitted. For step-by-step deployment see `DEPLOY.md`; for the debugging history
see `TROUBLESHOOTING.md`.
