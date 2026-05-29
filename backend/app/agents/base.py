from abc import ABC, abstractmethod
from typing import Any

from app.services.llm_service import LLMService


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm = llm_service or LLMService()

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError
