import hashlib
import logging

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.indexing.lexical_store import LexicalStore
from app.indexing.vector_store import VectorStore
from app.ingestion.pipeline import run_ingestion
from app.models import DeleteResponse, DocumentListResponse, DocumentStatus, IngestJobResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _doc_id_from_file(filename: str, content_hash: str) -> str:
    """Stable doc ID: slug of filename + first 8 chars of content hash."""
    slug = filename.lower().replace(" ", "-").replace(".pdf", "")
    return f"{slug}-{content_hash[:8]}"


@router.post("", response_model=IngestJobResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Derive stable doc_id from content hash (idempotent re-uploads)
    content_hash = hashlib.sha256(content).hexdigest()
    doc_id = _doc_id_from_file(file.filename, content_hash)

    # Persist the file
    pdf_path = settings.upload_dir / f"{doc_id}.pdf"
    async with aiofiles.open(pdf_path, "wb") as f:
        await f.write(content)

    # Register in SQLite before background task starts
    lexical = LexicalStore(settings)
    lexical.create_document(doc_id, file.filename)

    # Kick off ingestion in the background
    background_tasks.add_task(
        run_ingestion,
        pdf_path=pdf_path,
        doc_id=doc_id,
        filename=file.filename,
        settings=settings,
    )

    logger.info("Accepted upload: %s -> doc_id=%s", file.filename, doc_id)
    return IngestJobResponse(doc_id=doc_id, filename=file.filename)


@router.get("", response_model=DocumentListResponse)
def list_documents(settings: Settings = Depends(get_settings)):
    return DocumentListResponse(documents=LexicalStore(settings).list_documents())


@router.get("/{doc_id}", response_model=DocumentStatus)
def get_document(doc_id: str, settings: Settings = Depends(get_settings)):
    doc = LexicalStore(settings).get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.delete("/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str, settings: Settings = Depends(get_settings)):
    lexical = LexicalStore(settings)
    vector = VectorStore(settings)

    # Idempotent: purge from every store even if the SQLite record is missing
    # (e.g. after an ephemeral-storage restart that left orphaned Qdrant vectors).
    await vector.delete_by_doc_id(doc_id)
    lexical.delete_document(doc_id)

    # Delete the PDF file
    pdf_path = settings.upload_dir / f"{doc_id}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()

    logger.info("Deleted document doc_id=%s", doc_id)
    return DeleteResponse(doc_id=doc_id, deleted=True)
