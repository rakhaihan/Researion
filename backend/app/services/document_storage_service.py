import re
from pathlib import Path
from uuid import UUID

from app.core.config import get_settings


class DocumentStorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_dir = Path(self.settings.document_storage_dir)

    def user_dir(self, user_id: UUID) -> Path:
        return self.base_dir / str(user_id)

    def document_dir(self, user_id: UUID, document_id: UUID) -> Path:
        return self.user_dir(user_id) / str(document_id)

    def build_storage_path(
        self,
        user_id: UUID,
        document_id: UUID,
        safe_filename: str,
    ) -> Path:
        directory = self.document_dir(user_id, document_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / safe_filename

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        name = Path(filename).name
        name = re.sub(r"[^\w.\- ]", "_", name).strip()
        return name[:200] or "document"

    def delete_document_files(self, user_id: UUID, document_id: UUID) -> None:
        directory = self.document_dir(user_id, document_id)
        if directory.exists():
            for child in directory.iterdir():
                if child.is_file():
                    child.unlink(missing_ok=True)
            directory.rmdir()
