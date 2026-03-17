from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentHistoryItem,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
)
def upload_document(
    payload: Annotated[DocumentUploadRequest, Depends(DocumentUploadRequest.as_form)],
    file: Annotated[UploadFile, File(...)],
    service: DocumentServiceDep,
    background_tasks: BackgroundTasks,
) -> DocumentUploadResponse:
    return service.upload_document(payload, file, background_tasks)


@router.get(
    "",
    response_model=list[DocumentHistoryItem],
    summary="Get document history",
)
def list_documents(service: DocumentServiceDep) -> list[DocumentHistoryItem]:
    return service.get_document_history()


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
)
def get_document(
    document_id: int,
    service: DocumentServiceDep,
) -> DocumentDetailResponse:
    return service.get_document_detail(document_id)
