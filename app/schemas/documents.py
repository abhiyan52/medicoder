from datetime import datetime
from typing import Any, Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field

from app.models import DocumentStatus


class DocumentUploadRequest(BaseModel):
    """Metadata required to upload a document."""

    title: str = Field(min_length=1, max_length=255)

    @classmethod
    def as_form(cls, title: str = Form(...)) -> "DocumentUploadRequest":
        # Build the request model from multipart form data.
        return cls(title=title)


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    file_url: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class ProcessedResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    extracted_code: Any
    hcc_code: Optional[Any] = None


class DocumentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    file_url: str
    status: DocumentStatus
    extracted_text: Optional[str] = None
    processed_results: list[ProcessedResultItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
