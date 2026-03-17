import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from google.cloud import firestore
from google.cloud.exceptions import GoogleCloudError

from app.config import settings
from app.graph.medicoder_pipeline import run as run_processing_pipeline
from app.schemas.documents import DocumentStatus, DocumentUploadRequest
from app.utils.storage import StorageBackend

logger = logging.getLogger(__name__)


def _encode_page_token(created_at: datetime, document_id: str) -> str:
    payload = {
        "created_at": created_at.isoformat(),
        "document_id": document_id,
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")


def _decode_page_token(page_token: str) -> tuple[datetime, str]:
    try:
        payload = json.loads(
            base64.urlsafe_b64decode(page_token.encode("utf-8")).decode("utf-8")
        )
        return datetime.fromisoformat(payload["created_at"]), payload["document_id"]
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid page_token",
        ) from exc


def _normalize_processed_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for index, result in enumerate(results, start=1):
        normalized.append(
            {
                "id": str(index),
                "extracted_code": {
                    "condition": result.get("condition"),
                    "code": result.get("code"),
                },
                "hcc_code": {"hcc_relevant": result.get("hcc_relevant")},
            }
        )
    return normalized


def process_document_background(document_id: str) -> None:
    """Heavy background processing task using Firestore."""
    db = firestore.Client(project=settings.PROJECT_ID)
    doc_ref = db.collection("documents").document(document_id)
    doc = doc_ref.get()

    if not doc.exists:
        logger.error(f"Background task: Document {document_id} not found in Firestore.")
        return

    try:
        # Mark processing
        doc_ref.update({
            "status": DocumentStatus.processing.value,
            "updated_at": datetime.now(timezone.utc)
        })

        logger.info("Starting processing pipeline", extra={"document_id": document_id})
        doc_dict = doc.to_dict()
        file_url = doc_dict.get("file_url")
        if not file_url:
            raise ValueError("Document is missing file_url")

        extracted_text = StorageBackend.read_document_text(file_url)
        results = run_processing_pipeline(extracted_text)

        # Mark processed
        doc_ref.update({
            "status": DocumentStatus.processed.value,
            "updated_at": datetime.now(timezone.utc),
            "processed_at": datetime.now(timezone.utc),
            "extracted_text": extracted_text,
            "processed_results": _normalize_processed_results(results),
        })
        logger.info("Finished processing pipeline", extra={"document_id": document_id})

    except (GoogleCloudError, OSError, ValueError) as exc:
        logger.exception(
            "Processing failed",
            extra={
                "document_id": document_id,
                "error": str(exc),
            },
        )
        doc_ref.update({
            "status": DocumentStatus.failed.value,
            "updated_at": datetime.now(timezone.utc)
        })


class DocumentService:
    """Encapsulates document-related business logic using Firestore."""

    def __init__(self) -> None:
        # Initialize Firestore client. It automatically picks up GCP credentials.
        self.db = firestore.Client(project=settings.PROJECT_ID)
        self.collection = self.db.collection("documents")

    def upload_document(
        self,
        payload: DocumentUploadRequest,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> dict:
        file_url = StorageBackend.save_document(file)
        doc_ref = None
        
        now = datetime.now(timezone.utc)
        doc_data = {
            "title": payload.title,
            "file_url": file_url,
            "status": DocumentStatus.uploaded.value,
            "created_at": now,
            "updated_at": now,
        }

        try:
            # Create a new document in Firestore
            _, doc_ref = self.collection.add(doc_data)
            
            # Queue the background processing
            background_tasks.add_task(process_document_background, doc_ref.id)

            # Update status to queued
            doc_data["status"] = DocumentStatus.queued.value
            doc_data["updated_at"] = datetime.now(timezone.utc)
            doc_ref.update({
                "status": doc_data["status"],
                "updated_at": doc_data["updated_at"]
            })
            
            # Return data formatted for the schema
            doc_data["id"] = doc_ref.id
            return doc_data

        except Exception as exc:
            if doc_ref is not None:
                try:
                    doc_ref.delete()
                except Exception:
                    logger.exception(
                        "Failed to rollback Firestore document after upload failure",
                        extra={"document_id": doc_ref.id},
                    )

            try:
                StorageBackend.delete_document(file_url)
            except Exception:
                logger.exception(
                    "Failed to rollback stored document after upload failure",
                    extra={"file_url": file_url},
                )

            logger.exception(
                "Failed to save document to Firestore",
                extra={"error": str(exc)},
            )
            raise HTTPException(status_code=500, detail="Database error occurred.")

    def get_document_history(
        self,
        page_size: int = 50,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        safe_page_size = max(1, min(page_size, 100))
        query = self.collection.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        ).order_by("__name__", direction=firestore.Query.DESCENDING)

        if page_token:
            created_at, document_id = _decode_page_token(page_token)
            query = query.start_after({"created_at": created_at, "__name__": document_id})

        docs = list(query.limit(safe_page_size).stream())
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)

        next_page_token = None
        if docs:
            last_doc = docs[-1]
            last_data = last_doc.to_dict()
            created_at = last_data.get("created_at")
            if isinstance(created_at, datetime):
                next_page_token = _encode_page_token(created_at, last_doc.id)

        return {
            "items": results,
            "next_page_token": next_page_token,
        }

    def get_document_detail(self, document_id: str) -> dict:
        doc_ref = self.collection.document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
            
        data = doc.to_dict()
        data["id"] = doc.id
        # Ensure processed_results exists for the schema
        if "processed_results" not in data:
            data["processed_results"] = []
            
        return data
