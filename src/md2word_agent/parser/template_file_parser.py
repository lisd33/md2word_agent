from __future__ import annotations

from dataclasses import dataclass
import re

from md2word_agent.parser.docx_reader import DocxReader
from md2word_agent.parser.models import DocxDocumentRecord, ParagraphRecord, TemplateCandidate
from md2word_agent.planner import TemplateUnderstandingPlanner
from md2word_agent.specs import TemplateRequirement

HEADING_STYLE_HINTS = {
    "heading 1": 1,
    "heading 2": 2,
    "heading 3": 3,
    "标题 1": 1,
    "标题 2": 2,
    "标题 3": 3,
}

CANONICAL_SHORT_SECTIONS = {
    "abstract",
    "introduction",
    "related work",
    "method",
    "methods",
    "experiments",
    "results",
    "discussion",
    "conclusion",
    "references",
    "acknowledgment",
    "acknowledgement",
    "appendix",
}


@dataclass(slots=True)
class TemplateFileParseResult:
    requirement: TemplateRequirement
    candidates: list[TemplateCandidate]
    raw_record: DocxDocumentRecord


class TemplateFileParser:
    """Template parser that combines programmatic candidate extraction with LLM understanding."""

    def __init__(
        self,
        reader: DocxReader | None = None,
        understanding_planner: TemplateUnderstandingPlanner | None = None,
    ) -> None:
        self.reader = reader or DocxReader()
        self.understanding_planner = understanding_planner

    def extract_candidates(self, data: bytes) -> tuple[DocxDocumentRecord, list[TemplateCandidate]]:
        record = self.reader.read(data)
        candidates: list[TemplateCandidate] = []
        paragraphs = record.paragraphs
        for idx, paragraph in enumerate(paragraphs):
            if not paragraph.text:
                continue
            level = self._infer_heading_level(paragraph)
            if level is None:
                continue
            previous_text = paragraphs[idx - 1].text if idx > 0 else None
            next_text = paragraphs[idx + 1].text if idx + 1 < len(paragraphs) else None
            candidates.append(
                TemplateCandidate(
                    title=paragraph.text.strip(),
                    level=level,
                    style_id=paragraph.style_id,
                    style_name=paragraph.style_name,
                    numbering_level=paragraph.numbering_level,
                    previous_text=previous_text,
                    next_text=next_text,
                )
            )
        return record, candidates

    def parse(
        self,
        data: bytes,
        *,
        document_family: str = "unknown",
        rule_text: str | None = None,
    ) -> TemplateFileParseResult:
        record, candidates = self.extract_candidates(data)
        if self.understanding_planner is None:
            raise RuntimeError("TemplateFileParser requires an understanding planner for Stage 3 parsing.")
        requirement = self.understanding_planner.build_requirement(
            candidates=candidates,
            document_family=document_family,
            rule_text=rule_text,
        )
        requirement.formatting_constraints.update(self._extract_formatting_constraints(record))
        if "template_file" not in requirement.source_kinds:
            requirement.source_kinds.insert(0, "template_file")
        return TemplateFileParseResult(requirement=requirement, candidates=candidates, raw_record=record)

    def _extract_formatting_constraints(
        self,
        record: DocxDocumentRecord,
    ) -> dict[str, str | int | float | bool]:
        constraints = dict(record.layout_constraints)
        style_targets = {
            "title": self._find_style(record, style_ids={"Title"}, style_names={"title"}),
            "body": self._find_style(record, style_ids={"Normal"}, style_names={"normal", "body text", "正文"}),
            "caption": self._find_style(record, style_ids={"Caption"}, style_names={"caption", "题注"}),
            "heading_1": self._find_style(record, style_ids={"Heading1"}, style_names={"heading 1", "标题 1"}),
            "heading_2": self._find_style(record, style_ids={"Heading2"}, style_names={"heading 2", "标题 2"}),
        }
        for prefix, style in style_targets.items():
            if style is None:
                continue
            for key, value in style.formatting.items():
                constraints[f"{prefix}_{key}"] = value

        for style in record.styles.values():
            if style.style_type != "paragraph":
                continue
            style_key = self._style_export_key(style)
            if not style_key:
                continue
            for key, value in style.formatting.items():
                constraints[f"style_{style_key}_{key}"] = value
        return constraints

    def _find_style(
        self,
        record: DocxDocumentRecord,
        *,
        style_ids: set[str],
        style_names: set[str],
    ):
        normalized_ids = {item.lower() for item in style_ids}
        normalized_names = {item.lower() for item in style_names}
        for style in record.styles.values():
            if style.style_id.lower() in normalized_ids:
                return style
            if style.style_name and style.style_name.strip().lower() in normalized_names:
                return style
        return None

    def _style_export_key(self, style) -> str | None:
        raw = style.style_name or style.style_id
        if not raw:
            return None
        normalized = re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_")
        return normalized or None

    def _infer_heading_level(self, paragraph: ParagraphRecord) -> int | None:
        style_name = (paragraph.style_name or "").strip().lower()
        style_id = (paragraph.style_id or "").strip().lower()
        text = paragraph.text.strip()
        if style_name in HEADING_STYLE_HINTS:
            return HEADING_STYLE_HINTS[style_name]
        if style_id in {"heading1", "heading 1", "title1"}:
            return 1
        if style_id in {"heading2", "heading 2", "title2"}:
            return 2
        if style_id in {"heading3", "heading 3", "title3"}:
            return 3
        if re.match(r"^[IVXLC]+\.\s+", text):
            return 1
        if re.match(r"^[A-Z]\.\s+", text):
            return 2
        if re.match(r"^(\d+\.)+\d*\s+", text):
            return text.split()[0].count(".")
        if re.match(r"^\d+\s+", text):
            return 1
        if text.lower() in CANONICAL_SHORT_SECTIONS:
            return 1
        return None
