"""Document attachment REST endpoints — CRUD + MinIO integration.

Provides:
- POST /api/v1/structures/{id}/documents: register document (inspector+) per D-18
- GET /api/v1/structures/{id}/documents: list documents with presigned URLs (all roles) per D-18
- DELETE /api/v1/documents/{id}: delete document + MinIO object (admin only) per D-18
- GET /api/v1/documents/{id}/download: presigned download URL (all roles) per D-18

RBAC enforcement per D-12 permissions matrix:
- POST requires inspector+ role (T-03-12 mitigation)
- DELETE requires admin role (T-03-11 mitigation)
- GET endpoints require viewer+ role (any authenticated user)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.schemas.documents import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
)
from api.services import document_service

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.post(
    "/structures/{structure_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_document_endpoint(
    structure_id: uuid.UUID,
    body: DocumentCreate,
    current_user: UserModel = Depends(require_role("inspector")),
) -> DocumentResponse:
    """Register a document attachment for a structure (inspector+ role).

    Client flow: get presigned upload URL → upload to MinIO → register metadata via API.
    Creates a ProvenanceModel with source_type='manual' and the user's username.

    Returns 201 with the document metadata including id and provenance_id.
    """
    document = await document_service.register_document(
        structure_id=structure_id,
        data=body,
        user=current_user,
    )
    return DocumentResponse.model_validate(document)


@router.get(
    "/structures/{structure_id}/documents",
    response_model=DocumentListResponse,
)
async def list_documents_endpoint(
    structure_id: uuid.UUID,
    request: Request,
    current_user: UserModel = Depends(require_role("viewer")),
) -> DocumentListResponse:
    """List documents for a structure with presigned download URLs (all roles).

    Returns document metadata with presigned_download_url for each document,
    enabling direct download from MinIO (T-03-10: 2-hour expiry).
    """
    documents = await document_service.list_documents(structure_id)
    minio_service = request.app.state.minio

    items = []
    for doc in documents:
        doc_response = DocumentResponse.model_validate(doc)
        doc_response.presigned_download_url = minio_service.presigned_download_url(
            doc.minio_bucket, doc.minio_object_key
        )
        items.append(doc_response)

    return DocumentListResponse(items=items, total=len(items))


@router.delete("/documents/{document_id}")
async def delete_document_endpoint(
    document_id: uuid.UUID,
    request: Request,
    current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    """Delete a document record and its MinIO object (admin only).

    Removes the object from MinIO first, then deletes the DB record.
    Returns 404 if the document does not exist.
    """
    minio_service = request.app.state.minio
    deleted = await document_service.delete_document(document_id, minio_service)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )
    return {"status": "deleted"}


@router.get("/documents/{document_id}/download")
async def get_download_url_endpoint(
    document_id: uuid.UUID,
    request: Request,
    current_user: UserModel = Depends(require_role("viewer")),
) -> dict:
    """Get a presigned download URL for a document (all roles).

    Returns the presigned URL with 2-hour expiry (T-03-10: short expiry mitigation).
    Returns 404 if the document does not exist.
    """
    minio_service = request.app.state.minio
    url = await document_service.get_download_url(document_id, minio_service)
    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )
    return {"presigned_url": url, "expires_in_seconds": 7200}
