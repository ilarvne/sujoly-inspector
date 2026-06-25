"""Admin routes for document management."""

import os
import shutil
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks

from agent.loaders.pdf import aingest_pdf
from agent.loaders.text import aingest_text
from agent.memory.store import list_sources, delete_source
from agent.retrieval.hybrid import get_bm25_index
from agent.server_auth import get_current_user, UserProfile

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/ingest")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: UserProfile = Depends(get_current_user),
):
    """Upload and ingest a document."""
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=400, detail="Only .pdf and .txt files are supported"
        )

    # Save to a temporary file
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    async def _ingest():
        try:
            if suffix == ".pdf":
                await aingest_pdf(tmp_path, source_name=file.filename)
            else:
                await aingest_text(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    background_tasks.add_task(_ingest)
    return {"filename": file.filename, "status": "ingestion_started"}


@router.get("/documents")
async def get_documents(user: UserProfile = Depends(get_current_user)):
    """List unique sources in the vector store."""
    sources = list_sources()
    return {"sources": sources}


@router.delete("/documents")
async def remove_document(source: str, user: UserProfile = Depends(get_current_user)):
    """Delete all documents from a specific source (ChromaDB + BM25)."""
    delete_source(source)
    get_bm25_index().delete_by_source(source)
    return {"status": "deleted", "source": source}
