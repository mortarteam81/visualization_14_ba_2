from __future__ import annotations

import pytest

from utils.ai_providers.lmstudio import LMStudioClient, LMStudioError


def test_extract_content_returns_message_content() -> None:
    data = {
        "choices": [
            {
                "message": {
                    "content": '{"summary":"ok"}',
                }
            }
        ]
    }

    assert LMStudioClient._extract_content(data) == '{"summary":"ok"}'


def test_extract_content_raises_for_reasoning_only_response() -> None:
    data = {
        "choices": [
            {
                "message": {
                    "content": "",
                    "reasoning_content": "thinking only",
                }
            }
        ]
    }

    with pytest.raises(LMStudioError, match="reasoning_content만 반환"):
        LMStudioClient._extract_content(data)


def test_extract_content_raises_for_empty_response() -> None:
    data = {
        "choices": [
            {
                "message": {
                    "content": "",
                }
            }
        ]
    }

    with pytest.raises(LMStudioError, match="비어 있습니다"):
        LMStudioClient._extract_content(data)
