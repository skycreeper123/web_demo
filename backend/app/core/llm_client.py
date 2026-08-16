from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from web_demo.backend.app.core.config import normalize_base_url


@dataclass
class LLMResponse:
    text: str
    raw: dict[str, Any]


class OpenAICompatibleClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 120) -> None:
        self.base_url = normalize_base_url(base_url)
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def chat_with_image(self, system_prompt: str, user_text: str, image_data_url: str) -> LLMResponse:
        return self.chat_with_images(system_prompt, user_text, [image_data_url])

    def chat_with_images(self, system_prompt: str, user_text: str, image_data_urls: list[str]) -> LLMResponse:
        content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
        for image_data_url in image_data_urls:
            content.append({"type": "image_url", "image_url": {"url": image_data_url}})

        url = self.base_url.rstrip("/") + "/chat/completions"
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw_text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Network error: {exc.reason}") from exc

        raw = json.loads(raw_text)
        text = self._extract_text(raw)
        return LLMResponse(text=text, raw=raw)

    @staticmethod
    def _extract_text(raw: dict[str, Any]) -> str:
        choices = raw.get("choices") or []
        if not choices:
            return json.dumps(raw, ensure_ascii=False, indent=2)
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
            if parts:
                return "".join(parts)
        return json.dumps(raw, ensure_ascii=False, indent=2)
