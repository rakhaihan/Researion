import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: ChatOpenAI | None = None

    @property
    def client(self) -> ChatOpenAI:
        if self._client is None:
            if not self.settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not configured")
            self._client = ChatOpenAI(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                temperature=self.settings.llm_temperature,
            )
        return self._client

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = await self.client.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            content = str(response.content)
            return self._parse_json(content, fallback or {})
        except Exception as exc:
            logger.warning("LLM generation failed, using fallback: %s", exc)
            return fallback or {}

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        return str(response.content)

    @staticmethod
    def _parse_json(content: str, fallback: dict[str, Any]) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)

        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group())
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass

        return fallback
