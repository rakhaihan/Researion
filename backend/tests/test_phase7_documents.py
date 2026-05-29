import io
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile

from app.agents.search_agent import SearchAgent
from app.core.config import Settings
from app.db.models import Document, DocumentChunk, DocumentStatus, ResearchSourceMode
from app.schemas.documents import RAGChunkResult, ResearchSourceMode as ResearchSourceModeSchema
from app.schemas.research import ResearchCreate, ResearchDepth, ResearchType
from app.services.document_processing_service import DocumentProcessingService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.research_service import ResearchService
from app.utils.citations import build_sources_markdown_section


@pytest.fixture
def document_settings(tmp_path):
    return Settings(
        document_storage_dir=str(tmp_path / "documents"),
        max_document_size_mb=10,
        document_chunk_size=100,
        document_chunk_overlap=20,
        embedding_provider="mock",
    )


def test_mock_embedding_is_deterministic():
    service = EmbeddingService(Settings(embedding_provider="mock"))
    a = service._mock_embed("hello world")
    b = service._mock_embed("hello world")
    c = service._mock_embed("other text")
    assert a == b
    assert a != c


def test_chunk_text_file(document_settings, tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("A" * 250, encoding="utf-8")
    processor = DocumentProcessingService(document_settings)
    pages = processor.extract_text(txt, "text/plain")
    chunks = processor.chunk_pages(pages)
    assert len(chunks) >= 2
    assert chunks[0]["chunk_index"] == 0


@pytest.mark.asyncio
async def test_upload_txt_success(document_settings, tmp_path):
    service = DocumentService()
    service.settings = document_settings
    service.storage.base_dir = Path(document_settings.document_storage_dir)

    user_id = uuid4()
    content = b"Sample knowledge base text for testing upload."
    upload = UploadFile(
        filename="notes.txt",
        file=io.BytesIO(content),
        headers={"content-type": "text/plain"},
    )

    now = datetime.now(UTC)

    def assign_document_fields(obj) -> None:
        if isinstance(obj, Document):
            obj.id = uuid4()
            obj.created_at = now
            obj.updated_at = now

    db = AsyncMock()
    db.add = MagicMock(side_effect=assign_document_fields)
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    with patch.object(service, "_enqueue_processing", AsyncMock()):
        result = await service.upload_document(db, user_id, upload)

    assert result.original_filename == "notes.txt"
    assert result.status == DocumentStatus.UPLOADED


@pytest.mark.asyncio
async def test_upload_file_too_large_rejected(document_settings):
    service = DocumentService()
    service.settings = Settings(
        document_storage_dir=document_settings.document_storage_dir,
        max_document_size_mb=1,
    )
    data = b"x" * (2 * 1024 * 1024)
    upload = UploadFile(
        filename="big.txt",
        file=io.BytesIO(data),
        headers={"content-type": "text/plain"},
    )

    with pytest.raises(HTTPException) as exc:
        await service.upload_document(AsyncMock(), uuid4(), upload)
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_upload_unsupported_type_rejected(document_settings):
    service = DocumentService()
    service.settings = document_settings
    upload = UploadFile(
        filename="malware.exe",
        file=io.BytesIO(b"data"),
        headers={"content-type": "application/octet-stream"},
    )

    with pytest.raises(HTTPException) as exc:
        await service.upload_document(AsyncMock(), uuid4(), upload)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_document():
    service = DocumentService()
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)

    with pytest.raises(HTTPException) as exc:
        await service.get_document(db, uuid4(), uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_process_document_creates_chunks(document_settings, tmp_path):
    user_id = uuid4()
    doc_id = uuid4()
    file_path = tmp_path / "doc.txt"
    file_path.write_text("Paragraph one.\n\nParagraph two with more content.", encoding="utf-8")

    document = Document(
        id=doc_id,
        user_id=user_id,
        filename="doc.txt",
        original_filename="doc.txt",
        content_type="text/plain",
        file_size=file_path.stat().st_size,
        storage_path=str(file_path),
        status=DocumentStatus.UPLOADED,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    db = AsyncMock()
    select_result = MagicMock()
    select_result.scalar_one_or_none.return_value = document
    db.execute = AsyncMock(return_value=select_result)
    db.flush = AsyncMock()

    service = DocumentService()
    service.settings = document_settings
    service.processor = DocumentProcessingService(document_settings)

    await service.process_document(db, doc_id)
    assert document.status == DocumentStatus.PROCESSED
    assert db.add.called


@pytest.mark.asyncio
async def test_rag_retrieval_scoped_to_user_documents():
    from app.services.rag_service import RAGService

    user_id = uuid4()
    doc_id = uuid4()
    chunk_id = uuid4()

    chunk = DocumentChunk(
        id=chunk_id,
        document_id=doc_id,
        user_id=user_id,
        chunk_index=0,
        content="EV market growth in Southeast Asia",
        token_count=10,
        embedding=[0.1] * 64,
    )
    document = Document(
        id=doc_id,
        user_id=user_id,
        filename="report.pdf",
        original_filename="report.pdf",
        content_type="application/pdf",
        file_size=100,
        storage_path="/tmp/x",
        status=DocumentStatus.PROCESSED,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    rag = RAGService()
    rag.embedding_service.embed_text = AsyncMock(return_value=[0.1] * 64)
    rag.vector_store.search = AsyncMock(return_value=[(chunk, 0.92)])

    doc_result = MagicMock()
    doc_result.scalars.return_value.all.return_value = [document]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=doc_result)

    results = await rag.retrieve_relevant_chunks(db, user_id, "EV market", top_k=3)
    assert len(results) == 1
    assert results[0].filename == "report.pdf"
    rag.vector_store.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_documents_only_skips_web():
    agent = SearchAgent()
    agent.rag_service.retrieve_relevant_chunks = AsyncMock(
        return_value=[
            RAGChunkResult(
                chunk_id=uuid4(),
                document_id=uuid4(),
                filename="notes.txt",
                content="Internal note content",
                score=0.8,
                page_number=1,
            )
        ]
    )
    agent.search_service.search = AsyncMock(return_value=[{"title": "Web", "url": "https://x.com"}])

    results = await agent.run(
        [{"question": "What is the trend?", "priority": 1}],
        topic="EV market",
        research_source_mode="documents_only",
        document_ids=[str(uuid4())],
        user_id=uuid4(),
        db=AsyncMock(),
    )

    agent.search_service.search.assert_not_called()
    assert results[0]["source_type"] == "document"
    assert results[0]["citation_key"] == "S1"


@pytest.mark.asyncio
async def test_search_hybrid_includes_web_and_document():
    agent = SearchAgent()
    agent.rag_service.retrieve_relevant_chunks = AsyncMock(
        return_value=[
            RAGChunkResult(
                chunk_id=uuid4(),
                document_id=uuid4(),
                filename="notes.txt",
                content="Internal",
                score=0.7,
            )
        ]
    )
    agent.search_service.search = AsyncMock(
        return_value=[{"title": "Web hit", "url": "https://example.com/a", "snippet": "web"}]
    )

    results = await agent.run(
        [{"question": "Trend?", "priority": 1}],
        topic="EV",
        research_source_mode="hybrid",
        document_ids=[str(uuid4())],
        user_id=uuid4(),
        db=AsyncMock(),
    )

    agent.search_service.search.assert_called()
    types = {r["source_type"] for r in results}
    assert "document" in types
    assert "web" in types


def test_document_citation_in_sources_section():
    lines = build_sources_markdown_section(
        [
            {
                "citation_key": "S1",
                "title": "report.pdf, page 4",
                "url": "document://abc/chunk/xyz",
                "source_type": "document",
                "original_filename": "report.pdf",
                "page_number": 4,
            }
        ]
    )
    text = "\n".join(lines)
    assert "internal document" in text
    assert "report.pdf" in text
    assert "page 4" in text


@pytest.mark.asyncio
async def test_delete_document_removes_chunks(document_settings):
    user_id = uuid4()
    doc_id = uuid4()
    document = Document(
        id=doc_id,
        user_id=user_id,
        filename="a.txt",
        original_filename="a.txt",
        content_type="text/plain",
        file_size=10,
        storage_path=str(Path(document_settings.document_storage_dir) / "a.txt"),
        status=DocumentStatus.PROCESSED,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    db = AsyncMock()
    owned = MagicMock()
    owned.scalar_one_or_none.return_value = document
    db.execute = AsyncMock(return_value=owned)
    db.delete = AsyncMock()
    db.flush = AsyncMock()

    service = DocumentService()
    service.settings = document_settings
    service.storage.delete_document_files = MagicMock()

    await service.delete_document(db, doc_id, user_id)
    db.delete.assert_called_once_with(document)


@pytest.mark.asyncio
async def test_create_research_documents_only_validates_processed():
    user_id = uuid4()
    doc_id = uuid4()
    service = ResearchService()
    service.document_service.validate_documents_for_research = AsyncMock()

    db = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    payload = ResearchCreate(
        topic="Analyze uploaded market research notes",
        research_type=ResearchType.MARKET_RESEARCH,
        depth=ResearchDepth.STANDARD,
        research_source_mode=ResearchSourceModeSchema.DOCUMENTS_ONLY,
        document_ids=[doc_id],
    )
    project = await service.create_research(db, payload, user_id)
    service.document_service.validate_documents_for_research.assert_awaited_once()
    assert project.research_source_mode == ResearchSourceMode.DOCUMENTS_ONLY
    assert project.document_ids == [str(doc_id)]


def test_alembic_phase7_migration_exists():
    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    assert any("004_documents" in f.name for f in versions.glob("*.py"))
