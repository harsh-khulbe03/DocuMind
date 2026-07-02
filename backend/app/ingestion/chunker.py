import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models import Chunk


def _stable_chunk_id(doc_id: str, page: int, index: int, text: str) -> str:
    """Deterministic ID so re-ingesting the same PDF doesn't create duplicates."""
    payload = f"{doc_id}::{page}::{index}::{text[:64]}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


def chunk_pages(
    pages: list[dict],
    doc_id: str,
    filename: str,
    max_tokens: int = 512,
) -> list[Chunk]:
    """
    Split page text into overlapping chunks suitable for embedding.
    Uses character-based splitting as a proxy for tokens (4 chars ≈ 1 token).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_tokens * 4,
        chunk_overlap=128,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []

    for page_dict in pages:
        page_no = page_dict["page"]
        text = page_dict["text"]

        if not text.strip():
            continue

        splits = splitter.split_text(text)

        for i, split_text in enumerate(splits):
            split_text = split_text.strip()
            if len(split_text) < 40:  # skip trivially short fragments
                continue

            chunks.append(
                Chunk(
                    chunk_id=_stable_chunk_id(doc_id, page_no, i, split_text),
                    doc_id=doc_id,
                    filename=filename,
                    page=page_no,
                    text=split_text,
                    metadata={"page": page_no, "doc_id": doc_id, "filename": filename},
                )
            )

    return chunks
