from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

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
        return self.chat_with_media(
            system_prompt,
            user_text,
            [{"kind": "image", "url": image_data_url}],
        )

    def chat_with_media_urls(self, system_prompt: str, user_text: str, media_urls: list[str]) -> LLMResponse:
        return self.chat_with_media(
            system_prompt,
            user_text,
            [{"kind": "image", "url": media_url} for media_url in media_urls],
        )

    def chat_with_media(self, system_prompt: str, user_text: str, media_items: list[dict[str, str]]) -> LLMResponse:
        content: list[dict[str, Any]] = [{"type": "text", "text": self._build_prompt_text(system_prompt, user_text)}]
        for item in media_items:
            media_kind = str(item.get("kind") or "image").strip().lower()
            media_url = str(item.get("url") or "").strip()
            self._validate_media_url(media_url, media_kind)
            if media_kind == "video":
                content.append({"type": "video_url", "video_url": {"url": media_url}})
            else:
                content.append({"type": "image_url", "image_url": {"url": media_url}})

        url = self.base_url.rstrip("/") + "/chat/completions"
        body = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": content},
            ],
            "stream": False,
            "temperature": 0.3,
        }
        headers = {
            "Accept": "application/json",
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
    def _build_prompt_text(system_prompt: str, user_text: str) -> str:
        system_text = system_prompt.strip()
        user_content = user_text.strip()
        if system_text and user_content:
            return f"{system_text}\n\n{user_content}"
        return system_text or user_content

    @staticmethod
    def _validate_media_url(media_url: str, media_kind: str = "image") -> None:
        text = str(media_url).strip()
        if text.startswith("data:") and ";base64," in text:
            return
        parsed = urlparse(text)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return
        if media_kind == "video":
            raise RuntimeError("Video input must be a publicly accessible http(s) URL or a base64 data URL.")
        raise RuntimeError("Image input must be a publicly accessible http(s) URL or a base64 data URL.")

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
