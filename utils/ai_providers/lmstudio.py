from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


class LMStudioError(RuntimeError):
    """Raised when LM Studio cannot complete an inference request."""


@dataclass(frozen=True)
class LMStudioConfig:
    base_url: str
    model: str | None
    api_key: str | None
    timeout_seconds: int = 60


class LMStudioClient:
    """Small OpenAI-compatible client for LM Studio local server."""

    def __init__(self, config: LMStudioConfig | None = None) -> None:
        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1").rstrip("/")
        model = os.getenv("LMSTUDIO_MODEL") or None
        api_key = os.getenv("LMSTUDIO_API_KEY") or None
        self.config = config or LMStudioConfig(base_url=base_url, model=model, api_key=api_key)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _resolve_model(self) -> str:
        if self.config.model:
            return self.config.model

        try:
            response = requests.get(
                f"{self.config.base_url}/models",
                headers=self._headers(),
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LMStudioError(
                "LM Studio 모델 목록을 불러오지 못했습니다. 로컬 서버 실행 여부를 확인해 주세요."
            ) from exc

        data = response.json().get("data", [])
        if not data:
            raise LMStudioError(
                "LM Studio에 로드된 모델이 없습니다. LM Studio에서 모델을 먼저 로드해 주세요."
            )
        return data[0]["id"]

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        choices = data.get("choices", [])
        if not choices:
            raise LMStudioError("LM Studio 응답에 choices가 없습니다.")

        message = choices[0].get("message", {}) or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        reasoning_content = message.get("reasoning_content")
        if isinstance(reasoning_content, str) and reasoning_content.strip():
            raise LMStudioError(
                "LM Studio 모델이 최종 답변(content) 없이 reasoning_content만 반환했습니다. "
                "Gemma 모델 설정 또는 프롬프트를 더 단순화해 보거나, reasoning 비노출 설정을 확인해 주세요."
            )

        raise LMStudioError("LM Studio 응답 본문이 비어 있습니다.")

    def chat_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 900,
    ) -> str:
        model = self._resolve_model()
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LMStudioError(
                "LM Studio 분석 요청에 실패했습니다. 서버 주소, 모델 로드 상태, 네트워크를 확인해 주세요."
            ) from exc

        data = response.json()
        return self._extract_content(data)
