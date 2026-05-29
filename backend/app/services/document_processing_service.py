from pathlib import Path

from pypdf import PdfReader

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExtractedPage:
    def __init__(self, text: str, page_number: int | None = None) -> None:
        self.text = text
        self.page_number = page_number


class DocumentProcessingService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def extract_text(self, file_path: Path, content_type: str) -> list[ExtractedPage]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf" or content_type == "application/pdf":
            return self._extract_pdf(file_path)
        if suffix in {".txt", ".md", ".markdown"} or content_type.startswith("text/"):
            return self._extract_text_file(file_path)
        raise ValueError(f"Unsupported file type: {suffix or content_type}")

    def chunk_pages(self, pages: list[ExtractedPage]) -> list[dict]:
        chunk_size = self.settings.document_chunk_size
        overlap = self.settings.document_chunk_overlap
        chunks: list[dict] = []
        chunk_index = 0

        for page in pages:
            text = page.text.strip()
            if not text:
                continue
            start = 0
            while start < len(text):
                end = min(len(text), start + chunk_size)
                piece = text[start:end].strip()
                if piece:
                    chunks.append(
                        {
                            "chunk_index": chunk_index,
                            "content": piece,
                            "token_count": max(1, len(piece) // 4),
                            "page_number": page.page_number,
                            "section_title": None,
                        }
                    )
                    chunk_index += 1
                if end >= len(text):
                    break
                start = max(0, end - overlap)

        return chunks

    def _extract_pdf(self, file_path: Path) -> list[ExtractedPage]:
        pages: list[ExtractedPage] = []
        reader = PdfReader(str(file_path))
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                logger.warning("PDF page %s extract failed: %s", index, exc)
                text = ""
            pages.append(ExtractedPage(text=text, page_number=index))
        return pages

    def _extract_text_file(self, file_path: Path) -> list[ExtractedPage]:
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = file_path.read_text(encoding=encoding)
                return [ExtractedPage(text=text, page_number=None)]
            except UnicodeDecodeError:
                continue
        raise ValueError("Unable to decode text file with supported encodings")
