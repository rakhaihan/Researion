from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, resolve_current_user
from app.db.models import User
from app.schemas.documents import DocumentDetailResponse, DocumentResponse, DocumentStatusResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service() -> DocumentService:
    return DocumentService()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    return await service.upload_document(db, current_user.id, file)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentResponse]:
    return await service.list_documents(db, current_user.id)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentDetailResponse:
    return await service.get_document(db, document_id, current_user.id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentStatusResponse:
    return await service.get_status(db, document_id, current_user.id)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: DocumentService = Depends(get_document_service),
) -> None:
    await service.delete_document(db, document_id, current_user.id)
