import json
import re
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

REPAIR_PROMPT = (
    "Your previous response was invalid JSON or did not match the required schema. "
    "Return ONLY valid JSON matching the schema described in the system prompt. "
    "Do not include markdown fences or commentary."
)


class LLMService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: ChatOpenAI | None = None

    @property
    def client(self) -> ChatOpenAI:
        if self._client is None:
            if not self.settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not configured")
            model_kwargs: dict[str, Any] = {}
            if self.settings.openai_api_key:
                model_kwargs["response_format"] = {"type": "json_object"}
            self._client = ChatOpenAI(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                temperature=self.settings.llm_temperature,
                model_kwargs=model_kwargs,
            )
        return self._client

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        model_type: type[T],
        fallback: T,
        *,
        max_retries: int = 2,
    ) -> tuple[T, list[str]]:
        warnings: list[str] = []
        last_error: str | None = None

        for attempt in range(max_retries + 1):
            prompt = user_prompt if attempt == 0 else f"{user_prompt}\n\n{REPAIR_PROMPT}"
            if last_error:
                prompt += f"\n\nValidation error: {last_error}"

            try:
                raw = await self._invoke_llm(system_prompt, prompt)
                data = self._parse_json(raw, {})
                if not data:
                    last_error = "empty JSON object"
                    continue
                parsed = model_type.model_validate(data)
                if attempt > 0:
                    warnings.append(f"Structured output recovered after {attempt} retry(s).")
                return parsed, warnings
            except ValidationError as exc:
                last_error = str(exc.errors()[:3])
                logger.warning(
                    "Structured output validation failed (attempt %s/%s): %s",
                    attempt + 1,
                    max_retries + 1,
                    last_error,
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning("LLM structured generation failed: %s", exc)
                break

        warnings.append(
            f"Using safe fallback for {model_type.__name__} after parse/validation failure."
        )
        return fallback, warnings

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            content = await self._invoke_llm(system_prompt, user_prompt)
            return self._parse_json(content, fallback or {})
        except Exception as exc:
            logger.warning("LLM generation failed, using fallback: %s", exc)
            return fallback or {}

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return await self._invoke_llm(system_prompt, user_prompt)

    async def _invoke_llm(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self.client.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            return str(response.content)
        except Exception:
            if not self.settings.openai_api_key:
                raise
            fallback_client = ChatOpenAI(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                temperature=self.settings.llm_temperature,
            )
            response = await fallback_client.ainvoke(
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
