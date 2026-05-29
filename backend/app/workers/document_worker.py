from uuid import UUID

from app.core.logging import get_logger, setup_logging
from app.db.database import AsyncSessionLocal
from app.services.document_service import DocumentService

logger = get_logger(__name__)


async def process_document_job(ctx, document_id: str) -> None:
    setup_logging()
    service = DocumentService()
    async with AsyncSessionLocal() as db:
        try:
            await service.process_document(db, UUID(document_id))
            await db.commit()
        except Exception:
            await db.rollback()
            raise
