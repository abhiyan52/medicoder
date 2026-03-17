import enum
from typing import Any
from sqlalchemy import DateTime, Integer, String, Text, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    failed = "failed"
    processed = "processed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        default=DocumentStatus.uploaded,
        nullable=False,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    processed_results: Mapped[list["ProcessedResult"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class ProcessedResult(Base):
    __tablename__ = "processed_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    extracted_code: Mapped[Any] = mapped_column(JSON, nullable=False)
    hcc_code: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    
    document: Mapped["Document"] = relationship(back_populates="processed_results")
