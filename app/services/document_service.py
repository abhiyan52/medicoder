import logging
import time
from datetime import datetime, timezone

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from google.cloud import firestore

from app.schemas.documents import DocumentStatus, DocumentUploadRequest
from app.utils.storage import StorageBackend

logger = logging.getLogger(__name__)


def process_document_background(document_id: str):
    """Heavy background processing task using Firestore."""
    db = firestore.Client()
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

        # Simulate heavy processing (e.g. LangGraph)
        logger.info("Starting processing pipeline", extra={"document_id": document_id})
        # We would use StorageBackend.read_document_text(doc_dict.get('file_url')) here!
        time.sleep(5)  # Placeholder

        # Mark processed
        doc_ref.update({
            "status": DocumentStatus.processed.value,
            "updated_at": datetime.now(timezone.utc),
            "processed_at": datetime.now(timezone.utc),
            # Mock extracted data update
            "extracted_text": "Sample extracted medical text from pipeline.",
            "processed_results": [
                {
                    "id": "1",
                    "extracted_code": {"code": "E11.9", "description": "Type 2 diabetes mellitus"},
                    "hcc_code": {"code": "19", "description": "Diabetes without Complication"}
                }
            ]
        })
        logger.info("Finished processing pipeline", extra={"document_id": document_id})

    except Exception as exc:
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
        self.db = firestore.Client()
        self.collection = self.db.collection("documents")

    def upload_document(
        self,
        payload: DocumentUploadRequest,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> dict:
        file_url = StorageBackend.save_document(file)
        
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

        except Exception as e:
            # If DB insert fails, cleanup file
            if hasattr(StorageBackend, 'delete_document'):
                StorageBackend.delete_document(file_url)
            logger.error(f"Failed to save document to Firestore: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred.")

    def get_document_history(self) -> list[dict]:
        # Return documents in reverse chronological order
        docs = self.collection.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        ).stream()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
            
        return results

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
