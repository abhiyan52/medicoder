import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile
from google.cloud import storage

from app.config import settings

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class StorageBackend:
    @staticmethod
    def save_document(file: UploadFile) -> str:
        """Saves a document either locally or to GCS based on configuration."""
        filename = f"{uuid.uuid4()}_{file.filename}"
        
        if settings.GCS_BUCKET_NAME:
            client = storage.Client()
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            blob = bucket.blob(f"uploads/{filename}")
            
            # Reset file pointer just in case
            file.file.seek(0)
            blob.upload_from_file(file.file, content_type=file.content_type)
            return f"gs://{settings.GCS_BUCKET_NAME}/uploads/{filename}"
        else:
            # Save locally
            file_path = UPLOAD_DIR / filename
            file.file.seek(0)
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            return f"local://uploads/{filename}"

    @staticmethod
    def read_document_text(file_url: str) -> str:
        """Reads the document content returning it as a string. Note: Only supports text files currently."""
        if file_url.startswith("gs://"):
            parts = file_url.replace("gs://", "").split("/")
            bucket_name = parts[0]
            blob_name = "/".join(parts[1:])
            
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.download_as_text()
            
        elif file_url.startswith("local://"):
            path = file_url.replace("local://", "")
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        
        return ""
