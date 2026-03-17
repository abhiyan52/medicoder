from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from app.auth import verify_token
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentHistoryPageResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService


# All routes on this router require Bearer-token verification via `verify_token`.
router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(verify_token)],
)


def get_document_service() -> DocumentService:
    return DocumentService()


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
)
MAX_FILE_SIZE = 10 * 1024  # 10 KB


def upload_document(
    payload: Annotated[DocumentUploadRequest, Depends(DocumentUploadRequest.as_form)],
    file: Annotated[UploadFile, File(...)],
    service: DocumentServiceDep,
    background_tasks: BackgroundTasks,
) -> DocumentUploadResponse:
    if file.content_type not in ("text/plain", "text/plain; charset=utf-8"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only plain text files (.txt) are supported.",
        )
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File size exceeds the {MAX_FILE_SIZE // 1024} KB limit.",
        )
    file.file.seek(0)
    return service.upload_document(payload, file, background_tasks)


@router.get(
    "",
    response_model=DocumentHistoryPageResponse,
    summary="Get document history",
)
def list_documents(
    service: DocumentServiceDep,
    page_size: int = 50,
    page_token: str | None = None,
) -> DocumentHistoryPageResponse:
    return service.get_document_history(page_size=page_size, page_token=page_token)


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
)
def get_document(
    document_id: str,
    service: DocumentServiceDep,
) -> DocumentDetailResponse:
    return service.get_document_detail(document_id)
