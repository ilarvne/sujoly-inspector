"""MinIO presigned URL endpoints.

Provides:
- POST /api/v1/minio/presign: generate presigned upload URL (1hr expiry)
- GET /api/v1/minio/presign/{object_name}: generate presigned download URL (2hr expiry)

INT-04: binary assets are served via MinIO presigned URLs, separate from PostGIS.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from api.config.settings import settings

router = APIRouter(prefix="/api/v1/minio", tags=["minio"])


class PresignUploadRequest(BaseModel):
    """Request body for generating a presigned upload URL."""

    bucket: str = Field(..., description="MinIO bucket name (e.g., sujoly-documents)")
    object_name: str = Field(..., description="Object key/path within the bucket")


class PresignResponse(BaseModel):
    """Response containing a presigned URL and its expiry."""

    presigned_url: str
    expires_in_seconds: int


@router.post("/presign", response_model=PresignResponse)
async def presign_upload(body: PresignUploadRequest, request: Request) -> PresignResponse:
    """Generate a presigned PUT URL for uploading an object to MinIO.

    Expiry: 1 hour (3600 seconds). Short-lived for security (T-02-02).
    """
    minio_service = request.app.state.minio
    url = minio_service.presigned_upload_url(body.bucket, body.object_name)
    return PresignResponse(presigned_url=url, expires_in_seconds=3600)


@router.get("/presign/{object_name:path}", response_model=PresignResponse)
async def presign_download(
    object_name: str,
    request: Request,
    bucket: str | None = None,
) -> PresignResponse:
    """Generate a presigned GET URL for downloading an object from MinIO.

    Expiry: 2 hours (7200 seconds). Longer for field inspection download scenarios.

    Args:
        object_name: Object key/path within the bucket (path parameter)
        bucket: Bucket name (defaults to settings.minio_bucket)
    """
    minio_service = request.app.state.minio
    bucket_name = bucket or settings.minio_bucket
    url = minio_service.presigned_download_url(bucket_name, object_name)
    return PresignResponse(presigned_url=url, expires_in_seconds=7200)
