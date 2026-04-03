from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from md2word_agent.specs.models import InputKind

RULE_HINTS = {
    "font",
    "fontsize",
    "font size",
    "line spacing",
    "spacing",
    "title",
    "heading",
    "citation",
    "references",
    "margin",
    "template",
    "format",
    "字体",
    "字号",
    "行距",
    "标题",
    "正文",
    "参考文献",
    "格式",
}

CONTENT_HINTS = {
    "abstract",
    "introduction",
    "method",
    "experiment",
    "conclusion",
    "we propose",
    "this paper",
    "research",
    "摘要",
    "引言",
    "方法",
    "实验",
    "结论",
    "研究",
}

STRUCTURED_SUFFIXES = {".json", ".yaml", ".yml"}
TEMPLATE_SUFFIXES = {".docx", ".dotx", ".doc"}
MARKDOWN_SUFFIXES = {".md", ".markdown"}


@dataclass(slots=True)
class InputPayload:
    name: str
    text: str | None = None
    path: str | None = None


@dataclass(slots=True)
class RoutedInput:
    payload: InputPayload
    kind: InputKind
    reasons: list[str]


class InputRouter:
    """Rule-first router for heterogeneous project inputs.

    This router is intentionally lightweight. It prefers deterministic signals and
    only exposes coarse-grained source kinds that downstream modules can consume.
    """

    def route_payload(self, payload: InputPayload) -> RoutedInput:
        reasons: list[str] = []

        if payload.path:
            path = Path(payload.path)
            suffix = path.suffix.lower()
            if suffix in TEMPLATE_SUFFIXES:
                reasons.append(f"file suffix {suffix} indicates a template file")
                return RoutedInput(payload, "template_file", reasons)
            if suffix in STRUCTURED_SUFFIXES:
                reasons.append(f"file suffix {suffix} indicates structured specification")
                return RoutedInput(payload, "structured_spec", reasons)
            if suffix in MARKDOWN_SUFFIXES:
                kind, rule_reason = self._classify_text(payload.text or path.stem)
                reasons.append(f"markdown payload routed as {kind}")
                reasons.extend(rule_reason)
                return RoutedInput(payload, kind, reasons)

        kind, rule_reason = self._classify_text(payload.text or payload.name)
        reasons.extend(rule_reason)
        return RoutedInput(payload, kind, reasons)

    def route_batch(self, payloads: Iterable[InputPayload]) -> list[RoutedInput]:
        routed = [self.route_payload(payload) for payload in payloads]
        kinds = {item.kind for item in routed if item.kind != "unknown"}
        if len(kinds) > 1:
            merged_reasons = [f"contains multiple source kinds: {sorted(kinds)}"]
            return [
                RoutedInput(item.payload, "mixed_input", merged_reasons + item.reasons)
                for item in routed
            ]
        return routed

    def _classify_text(self, text: str) -> tuple[InputKind, list[str]]:
        lowered = text.lower()
        reasons: list[str] = []
        rule_hits = sum(1 for hint in RULE_HINTS if hint in lowered)
        content_hits = sum(1 for hint in CONTENT_HINTS if hint in lowered)

        if rule_hits and content_hits:
            reasons.append(
                f"matched both rule hints ({rule_hits}) and content hints ({content_hits})"
            )
            return "mixed_input", reasons
        if rule_hits:
            reasons.append(f"matched rule hints ({rule_hits})")
            return "rule_text", reasons
        if content_hits:
            reasons.append(f"matched content hints ({content_hits})")
            return "content_draft", reasons
        if lowered.strip().startswith("{") or lowered.strip().startswith("["):
            reasons.append("looks like structured serialized content")
            return "structured_spec", reasons
        reasons.append("no strong routing signal detected")
        return "unknown", reasons
