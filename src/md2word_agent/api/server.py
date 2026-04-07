from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from md2word_agent.llm import resolve_provider

from .service import ParseAPIService


class APIServerHandler(BaseHTTPRequestHandler):
    service: ParseAPIService

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/providers":
            provider = resolve_provider(self.service.env_file)
            self._send_json(
                200,
                {
                    "default_provider": provider,
                    "supported_providers": ["moonshot", "minimax", "zhipu"],
                },
            )
            return
        self._send_json(404, {"error": f"Unknown route: {self.path}"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._read_json_body()
            if self.path == "/api/v1/parse/rules":
                payload = self.service.parse_rule_text(
                    text=body["text"],
                    document_family=body.get("document_family", "unknown"),
                    include_evidence=body.get("include_evidence", True),
                )
                self._send_json(200, payload)
                return
            if self.path == "/api/v1/parse/template":
                payload = self.service.parse_docx_template(
                    document_family=body.get("document_family", "unknown"),
                    provider=body.get("provider"),
                    docx_path=body.get("docx_path"),
                    docx_base64=body.get("docx_base64"),
                    rule_text=body.get("rule_text"),
                    include_candidates=body.get("include_candidates", True),
                )
                self._send_json(200, payload)
                return
            if self.path == "/api/v1/parse/template/merged":
                payload = self.service.parse_merged_template_spec(
                    document_family=body.get("document_family", "unknown"),
                    provider=body.get("provider"),
                    docx_path=body.get("docx_path"),
                    docx_base64=body.get("docx_base64"),
                    rule_text=body["rule_text"],
                    include_candidates=body.get("include_candidates", True),
                    include_evidence=body.get("include_evidence", True),
                )
                self._send_json(200, payload)
                return
            self._send_json(404, {"error": f"Unknown route: {self.path}"})
        except KeyError as exc:
            self._send_json(400, {"error": f"Missing field: {exc.args[0]}"})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover
            self._send_json(500, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_api_server(*, host: str = "127.0.0.1", port: int = 8000, env_file: str | Path | None = None) -> ThreadingHTTPServer:
    service = ParseAPIService(env_file=env_file)

    class BoundHandler(APIServerHandler):
        pass

    BoundHandler.service = service
    return ThreadingHTTPServer((host, port), BoundHandler)
