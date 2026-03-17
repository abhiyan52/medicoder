import logging
import time

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Document, DocumentStatus
from app.schemas.documents import DocumentUploadRequest
from app.utils.storage import DocumentStorageError, StorageBackend


logger = logging.getLogger(__name__)


def process_document_background(document_id: int):
    """Heavy background processing task."""
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return

        try:
            # Mark processing
            doc.status = DocumentStatus.processing
            db.commit()

            # Simulate heavy processing (e.g. LangGraph)
            logger.info("Starting processing pipeline", extra={"document_id": document_id})
            # We would use StorageBackend.read_document_text(doc.file_url) here right before processing!
            time.sleep(5)  # Placeholder

            # Mark processed
            doc.status = DocumentStatus.processed
            db.commit()
            logger.info("Finished processing pipeline", extra={"document_id": document_id})

        except (SQLAlchemyError, DocumentStorageError, ValueError, OSError) as exc:
            logger.exception(
                "Processing failed",
                extra={
                    "document_id": document_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            db.rollback()
            fresh_doc = db.get(Document, document_id)
            if fresh_doc is not None:
                fresh_doc.status = DocumentStatus.failed
                db.commit()

    finally:
        db.close()


class DocumentService:
    """Encapsulates document-related business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def upload_document(
        self,
        payload: DocumentUploadRequest,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> Document:
        file_url = StorageBackend.save_document(file)
        try:
            # Persist a newly uploaded document and return the stored record.
            document = Document(
                title=payload.title,
                file_url=file_url,
                status=DocumentStatus.uploaded,
            )
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            # Queue the background processing only after the document exists in the DB.
            background_tasks.add_task(process_document_background, document.id)

            # Update status to queued once the task has been scheduled.
            document.status = DocumentStatus.queued
            self.db.commit()
            self.db.refresh(document)
        except Exception:
            self.db.rollback()
            StorageBackend.delete_document(file_url)
            raise

        return document

    def get_document_history(self) -> list[Document]:
        # Return documents in reverse chronological order for history views.
        return (
            self.db.query(Document)
            .order_by(Document.created_at.desc(), Document.id.desc())
            .all()
        )

    def get_document_detail(self, document_id: int) -> Document:
        # Resolve a single document or raise a clean 404 for the API layer.
        document = self.db.get(Document, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return document
