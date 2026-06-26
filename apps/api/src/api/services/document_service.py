"""Document CRUD + MinIO integration service — async database operations.

Provides:
- register_document: create document with provenance (source_type='manual')
- get_document: retrieve a document by ID
- list_documents: list documents for a structure ordered by created_at DESC
- delete_document: remove DB record + MinIO object
- get_download_url: generate presigned download URL for a document

Architecture separation (INT-04): binary content lives in MinIO, not PostgreSQL.
This service coordinates DB operations with MinIO for object deletion and
presigned URL generation.
"""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import desc, select

from api.infrastructure.database import async_session
from api.models.document import DocumentModel
from api.models.provenance import ProvenanceModel
from api.models.user import UserModel
from api.schemas.documents import DocumentCreate
from api.services.minio_client import MinIOService

logger = structlog.get_logger(__name__)


async def register_document(
    structure_id: uuid.UUID,
    data: DocumentCreate,
    user: UserModel,
) -> DocumentModel:
    """Register a new document attachment with provenance tracking.

    Creates a ProvenanceModel with source_type='manual' and the user's username
    as contributor, then creates the DocumentModel with all metadata fields.

    Args:
        structure_id: UUID of the structure to attach the document to
        data: DocumentCreate with document metadata and MinIO object key
        user: the authenticated user registering the document

    Returns:
        The created DocumentModel with generated id, provenance_id, and timestamps.
    """
    async with async_session() as session:
        async with session.begin():
            # Create provenance record — every document has a source (DATA-07)
            provenance = ProvenanceModel(
                source_type="manual",
                source_reference=f"document:upload:{data.minio_object_key}",
                confidence_level="HIGH",
                contributor=user.username,
            )
            session.add(provenance)
            await session.flush()

            # Create document record with provenance link
            document = DocumentModel(
                structure_id=structure_id,
                document_type=data.document_type,
                title=data.title,
                language=data.language,
                minio_bucket=data.minio_bucket,
                minio_object_key=data.minio_object_key,
                file_size_bytes=data.file_size_bytes,
                uploaded_by=user.username,
                provenance_id=provenance.id,
            )
            session.add(document)
            await session.flush()
            await session.refresh(document)

            logger.info(
                "document_registered",
                document_id=str(document.id),
                structure_id=str(structure_id),
                document_type=data.document_type,
            )
            return document


async def get_document(document_id: uuid.UUID) -> DocumentModel | None:
    """Retrieve a document record by ID.

    Args:
        document_id: UUID of the document

    Returns:
        DocumentModel if found, None if not found.
    """
    async with async_session() as session:
        result = await session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        return result.scalar_one_or_none()


async def list_documents(structure_id: uuid.UUID) -> list[DocumentModel]:
    """List documents for a structure ordered by created_at DESC.

    Args:
        structure_id: UUID of the structure

    Returns:
        List of DocumentModel instances for the given structure.
    """
    async with async_session() as session:
        result = await session.execute(
            select(DocumentModel)
            .where(DocumentModel.structure_id == structure_id)
            .order_by(desc(DocumentModel.created_at))
        )
        return list(result.scalars().all())


async def delete_document(
    document_id: uuid.UUID,
    minio_service: MinIOService,
) -> bool:
    """Delete a document record and its MinIO object.

    First removes the object from MinIO, then deletes the DB record.
    If the document is not found, returns False without attempting MinIO deletion.

    Args:
        document_id: UUID of the document to delete
        minio_service: MinIOService instance for object deletion

    Returns:
        True if document was found and deleted, False if not found.
    """
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
            document = result.scalar_one_or_none()
            if document is None:
                return False

            # Remove object from MinIO first (T-03-11: only admin can reach this)
            minio_service.client.remove_object(
                document.minio_bucket, document.minio_object_key
            )

            # Delete DB record
            await session.delete(document)

            logger.info(
                "document_deleted",
                document_id=str(document_id),
                minio_object_key=document.minio_object_key,
            )
            return True


async def get_download_url(
    document_id: uuid.UUID,
    minio_service: MinIOService,
) -> str | None:
    """Generate a presigned download URL for a document.

    Args:
        document_id: UUID of the document
        minio_service: MinIOService instance for URL generation

    Returns:
        Presigned download URL string if document found, None if not found.
    """
    async with async_session() as session:
        result = await session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        document = result.scalar_one_or_none()
        if document is None:
            return None

        return minio_service.presigned_download_url(
            document.minio_bucket, document.minio_object_key
        )
