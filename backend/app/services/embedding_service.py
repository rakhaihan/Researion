import hashlib
import math

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

MOCK_EMBEDDING_DIM = 64


class EmbeddingService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def embed_text(self, text: str) -> list[float]:
        if self.settings.embedding_provider == "openai" and self.settings.openai_api_key:
            return await self._openai_embed(text)
        return self._mock_embed(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(text) for text in texts]

    async def _openai_embed(self, text: str) -> list[float]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json={
                        "model": self.settings.openai_embedding_model,
                        "input": text[:8000],
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as exc:
            logger.warning("OpenAI embedding failed, using mock: %s", exc)
            return self._mock_embed(text)

    @staticmethod
    def _mock_embed(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for i in range(MOCK_EMBEDDING_DIM):
            byte = digest[i % len(digest)]
            values.append((byte / 255.0) * 2 - 1)
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
        norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (norm_a * norm_b)
