"""MinIO object storage service.

Provides:
- ensure_bucket: create bucket if it doesn't exist
- presigned_upload_url: generate presigned PUT URL (1 hour expiry)
- presigned_download_url: generate presigned GET URL (2 hour expiry)

Architecture separation (INT-04): binary assets (imagery, documents, photos)
live in MinIO, not in PostgreSQL. PostGIS stores only vector features.
"""

from datetime import timedelta

from minio import Minio


class MinIOService:
    """Wrapper around the MinIO SDK for presigned URL generation and bucket management.

    Bucket structure:
    - sujoly-imagery: COGs, satellite scenes, water index composites (STAC items)
    - sujoly-documents: Scanned passports, inspection reports, spreadsheets
    - sujoly-photos: Field inspection photos, voice note attachments
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
    ):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def ensure_bucket(self, bucket_name: str) -> None:
        """Create bucket if it doesn't exist."""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def presigned_upload_url(
        self,
        bucket: str,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """Generate a presigned PUT URL for uploading an object.

        Expiry: 1 hour (short-lived for security — T-02-02 mitigation).
        """
        return self.client.presigned_put_object(bucket, object_name, expires=expires)

    def presigned_download_url(
        self,
        bucket: str,
        object_name: str,
        expires: timedelta = timedelta(hours=2),
    ) -> str:
        """Generate a presigned GET URL for downloading an object.

        Expiry: 2 hours (longer for field inspection download scenarios).
        """
        return self.client.presigned_get_object(bucket, object_name, expires=expires)
