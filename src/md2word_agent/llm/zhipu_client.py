from __future__ import annotations

import json
from urllib import error, request

from .config import ZhipuConfig
from .kimi_client import _parse_json_content


class ZhipuClient:
    def __init__(self, config: ZhipuConfig) -> None:
        self.config = config

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        if not self.config.api_key or self.config.api_key == "your_zhipu_api_key":
            raise RuntimeError("ZHIPU_API_KEY is not configured. Please update md2word_agent/.env or your shell environment.")

        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.config.base_url.rstrip("/") + "/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Zhipu API request failed: {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Zhipu API request failed: {exc.reason}") from exc

        content = data["choices"][0]["message"]["content"]
        return _parse_json_content(content)
