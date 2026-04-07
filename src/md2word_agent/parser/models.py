from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ParagraphRecord:
    text: str
    style_id: str | None = None
    style_name: str | None = None
    numbering_level: int | None = None


@dataclass(slots=True)
class StyleRecord:
    style_id: str
    style_name: str | None = None
    based_on: str | None = None
    style_type: str | None = None
    formatting: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(slots=True)
class DocxDocumentRecord:
    paragraphs: list[ParagraphRecord] = field(default_factory=list)
    styles: dict[str, StyleRecord] = field(default_factory=dict)
    layout_constraints: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(slots=True)
class TemplateCandidate:
    title: str
    level: int
    style_id: str | None = None
    style_name: str | None = None
    numbering_level: int | None = None
    previous_text: str | None = None
    next_text: str | None = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "level": self.level,
            "style_id": self.style_id,
            "style_name": self.style_name,
            "numbering_level": self.numbering_level,
            "previous_text": self.previous_text,
            "next_text": self.next_text,
        }
