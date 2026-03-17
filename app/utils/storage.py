import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from app.utils.logger import logger

from app.config import settings

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DocumentStorageError(Exception):
    """Raised when document storage operations fail."""


class StorageBackend:
    @staticmethod
    def save_document(file: UploadFile) -> str:
        """Saves a document either locally or to GCS based on configuration."""
        filename = f"{uuid.uuid4()}_{file.filename}"

        if settings.GCS_BUCKET_NAME:
            try:
                from google.cloud import storage
                from google.cloud.exceptions import GoogleCloudError
            except ImportError as exc:
                raise DocumentStorageError(
                    "google-cloud-storage is required for GCS document uploads"
                ) from exc

            try:
                client = storage.Client()
                bucket = client.bucket(settings.GCS_BUCKET_NAME)
                blob = bucket.blob(f"uploads/{filename}")

                # Reset file pointer just in case
                file.file.seek(0)
                blob.upload_from_file(file.file, content_type=file.content_type)
                return f"gs://{settings.GCS_BUCKET_NAME}/uploads/{filename}"
            except (GoogleCloudError, Exception) as exc:
                logger.exception(
                    "Failed to upload document to GCS",
                    filename=filename,
                    bucket_name=settings.GCS_BUCKET_NAME,
                    error=str(exc),
                )
                raise DocumentStorageError(
                    f"Failed to store document in GCS: {filename}"
                ) from exc

        file_path = UPLOAD_DIR / filename
        try:
            file.file.seek(0)
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            return f"local://uploads/{filename}"
        except OSError as exc:
            if file_path.exists():
                file_path.unlink(missing_ok=True)
            logger.exception(
                "Failed to store document locally",
                filename=filename,
                error=str(exc),
            )
            raise DocumentStorageError(
                f"Failed to store document locally: {filename}"
            ) from exc

    @staticmethod
    def read_document_text(file_url: str) -> str:
        """Reads the document content returning it as a string. Note: Only supports text files currently."""
        if file_url.startswith("gs://"):
            try:
                from google.cloud import storage
                from google.cloud.exceptions import GoogleCloudError, NotFound
            except ImportError as exc:
                raise DocumentStorageError(
                    "google-cloud-storage is required for GCS document reads"
                ) from exc

            parts = file_url.replace("gs://", "").split("/")
            bucket_name = parts[0]
            blob_name = "/".join(parts[1:])

            try:
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                return blob.download_as_text()
            except (NotFound, GoogleCloudError) as exc:
                raise DocumentStorageError(
                    f"Failed to read GCS document at {file_url}: {exc}"
                ) from exc

        if file_url.startswith("local://"):
            path = file_url.replace("local://", "")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except (FileNotFoundError, OSError) as exc:
                raise DocumentStorageError(
                    f"Failed to read local document at {file_url}: {exc}"
                ) from exc

        raise ValueError(f"Unsupported document URL scheme: {file_url}")

    @staticmethod
    def delete_document(file_url: str) -> None:
        """Deletes a stored document if persistence needs to be rolled back."""
        if file_url.startswith("gs://"):
            try:
                from google.cloud import storage
                from google.cloud.exceptions import GoogleCloudError
            except ImportError as exc:
                raise DocumentStorageError(
                    "google-cloud-storage is required for GCS document deletes"
                ) from exc

            try:
                parts = file_url.replace("gs://", "").split("/")
                bucket_name = parts[0]
                blob_name = "/".join(parts[1:])
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                bucket.blob(blob_name).delete()
                return
            except GoogleCloudError as exc:
                raise DocumentStorageError(
                    f"Failed to delete GCS document at {file_url}: {exc}"
                ) from exc

        if file_url.startswith("local://"):
            path = Path(file_url.replace("local://", ""))
            try:
                path.unlink(missing_ok=True)
                return
            except OSError as exc:
                raise DocumentStorageError(
                    f"Failed to delete local document at {file_url}: {exc}"
                ) from exc

        raise ValueError(f"Unsupported document URL scheme: {file_url}")
