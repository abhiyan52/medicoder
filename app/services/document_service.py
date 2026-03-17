import time
from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Document, DocumentStatus
from app.schemas.documents import DocumentUploadRequest
from app.utils.storage import StorageBackend


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
            print(f"Starting processing pipeline for Document {document_id}...")
            # We would use StorageBackend.read_document_text(doc.file_url) here right before processing!
            time.sleep(5)  # Placeholder

            # Mark processed
            doc.status = DocumentStatus.processed
            db.commit()
            print(f"Finished processing pipeline for Document {document_id}")

        except Exception as e:
            print(f"Processing failed for Document {document_id}: {e}")
            db.rollback()
            doc.status = DocumentStatus.failed
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

        # Persist a newly uploaded document and return the stored record.
        document = Document(
            title=payload.title,
            file_url=file_url,
            status=DocumentStatus.uploaded
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        # Queue the background processing
        background_tasks.add_task(process_document_background, document.id)

        # Update status to queued
        document.status = DocumentStatus.queued
        self.db.commit()
        self.db.refresh(document)

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
