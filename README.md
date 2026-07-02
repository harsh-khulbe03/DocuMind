# DocuMind

Upload PDFs. Ask questions. Get cited, source-grounded answers.
Hybrid retrieval (semantic + BM25) with a cross-encoder reranker. Runs fully local with Ollama, or free in the cloud with Groq.

**Live demo:** frontend on Vercel, backend on Hugging Face Spaces, vectors in Qdrant Cloud, chat via Groq.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Docling, LangChain text-splitters |
| Vector index | Qdrant (local) / Qdrant Cloud (deployed) |
| Lexical index | SQLite FTS5 (BM25) |
| Embeddings | Ollama `nomic-embed-text` (local) / sentence-transformers `all-MiniLM-L6-v2` (deployed) / AWS Bedrock |
| Reranker | sentence-transformers cross-encoder |
| LLM | Ollama (local) / Groq (free hosted) / AWS Bedrock |
| Frontend | React 18, Vite, TailwindCSS, shadcn/ui |
| Infra | Docker Compose (local); Vercel + Hugging Face Spaces + Qdrant Cloud (deployed) |

## Quick start

### 1. Prerequisites

- Docker + Docker Compose
- Ollama running locally with the models pulled:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env if needed — defaults work for Ollama out of the box
```

Provider options in `.env`:

```
# Groq (free hosted LLM) — key at https://console.groq.com
LLM_PROVIDER=groq
GROQ_API_KEY=...
EMBEDDING_PROVIDER=local      # runs sentence-transformers in-process

# AWS Bedrock
LLM_PROVIDER=bedrock
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

`LLM_PROVIDER` (chat) and `EMBEDDING_PROVIDER` are independent: e.g. Groq for chat with `local` embeddings.

### 3. Start

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Qdrant dashboard: http://localhost:6333/dashboard

### 4. Use

1. Open http://localhost:5173
2. Drop a PDF into the upload zone — status shows "Processing" then "Ready"
3. Ask a question in the chat
4. Expand source chips below each answer to see the exact passages used

## How it works

```
Upload PDF
  └─► Docling parses pages (text layer; OCR disabled by default)
        └─► RecursiveCharacterTextSplitter produces chunks
              └─► Chunks embedded → Qdrant (vector)
              └─► Chunks indexed → SQLite FTS5 (lexical)

Query
  └─► Vector search (Qdrant, top 20)  ─┐
  └─► Lexical search (BM25, top 20)   ─┴─► Reciprocal Rank Fusion
                                                └─► Cross-encoder reranker (top 5)
                                                      └─► Grounded LLM answer (streaming SSE),
                                                          declines when context is insufficient
```

## Deployment (free)

Deployed on free tiers with local Ollama swapped for hosted services:

- **Frontend** → Vercel (set `VITE_API_URL` to the backend URL)
- **Backend** → Hugging Face Spaces (Docker; `LLM_PROVIDER=groq`, `EMBEDDING_PROVIDER=local`)
- **Vectors** → Qdrant Cloud (free 1 GB cluster)
- **Chat** → Groq (free API); **embeddings + reranker** run in-process in the backend

Full step-by-step in [DEPLOY.md](DEPLOY.md). Known free-tier limitation: Hugging Face
Spaces storage is ephemeral, so the SQLite document list and lexical index reset on
restart (Qdrant vectors persist). See DEPLOY.md for durable-storage options.

## Development (without Docker)

```bash
# Backend
cd backend
cp ../.env.example .env
uv sync
uv run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Project structure

```
documind/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py          # FastAPI app
│       ├── config.py        # Settings
│       ├── models.py        # Pydantic schemas
│       ├── ingestion/       # parse → chunk → index
│       ├── indexing/        # Qdrant + SQLite FTS5 + embedder
│       ├── retrieval/       # vector + lexical + RRF + reranker
│       ├── llm/             # Ollama + Groq + Bedrock providers
│       ├── generation/      # prompt + answer streaming
│       └── api/             # FastAPI routers
└── frontend/
    └── src/
        ├── api/             # API client
        ├── hooks/           # useDocuments, useChat
        └── components/      # UI components
```
