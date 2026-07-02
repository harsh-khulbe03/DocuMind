# DocuMind

Upload PDFs. Ask questions. Get cited, source-grounded answers.
Hybrid retrieval (semantic + BM25) with a cross-encoder reranker. Supports Ollama (local) and AWS Bedrock.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Docling, LangChain text-splitters |
| Vector index | Qdrant |
| Lexical index | SQLite FTS5 (BM25) |
| Reranker | sentence-transformers cross-encoder |
| LLM | Ollama (local) or AWS Bedrock |
| Frontend | React 18, Vite, TailwindCSS, shadcn/ui |
| Infra | Docker Compose |

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

For Bedrock, set in `.env`:
```
LLM_PROVIDER=bedrock
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

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
  └─► Docling parses pages (OCR if needed)
        └─► RecursiveCharacterTextSplitter produces chunks
              └─► Chunks embedded → Qdrant (vector)
              └─► Chunks indexed → SQLite FTS5 (lexical)

Query
  └─► Vector search (Qdrant, top 20)  ─┐
  └─► Lexical search (BM25, top 20)   ─┴─► Reciprocal Rank Fusion
                                                └─► Cross-encoder reranker (top 5)
                                                      └─► Confidence gate
                                                            └─► LLM answer (streaming SSE)
```

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
│       ├── llm/             # Ollama + Bedrock providers
│       ├── generation/      # prompt + answer streaming
│       └── api/             # FastAPI routers
└── frontend/
    └── src/
        ├── api/             # API client
        ├── hooks/           # useDocuments, useChat
        └── components/      # UI components
```
