from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

InputKind = Literal[
    "template_file",
    "rule_text",
    "content_draft",
    "structured_spec",
    "mixed_input",
    "unknown",
]

SectionAction = Literal["keep", "optionalize", "remove", "add", "split", "merge"]


@dataclass(slots=True)
class TemplateSectionRequirement:
    title: str
    level: int
    required: bool = True
    section_type: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TemplateRequirement:
    document_family: str
    source_kinds: list[InputKind] = field(default_factory=list)
    required_sections: list[TemplateSectionRequirement] = field(default_factory=list)
    optional_sections: list[TemplateSectionRequirement] = field(default_factory=list)
    citation_style: str | None = None
    formatting_constraints: dict[str, str | int | float | bool] = field(default_factory=dict)
    figure_requirements: dict[str, int | str | bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ContentIntent:
    title: str | None = None
    domain: str | None = None
    paper_type: str | None = None
    keywords: list[str] = field(default_factory=list)
    has_experiments: bool | None = None
    has_figures: bool | None = None
    source_summary: str | None = None
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class DocumentSectionPlan:
    title: str
    level: int
    action: SectionAction = "keep"
    section_type: str | None = None
    summary: str | None = None
    children: list["DocumentSectionPlan"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "level": self.level,
            "action": self.action,
            "section_type": self.section_type,
            "summary": self.summary,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass(slots=True)
class DocumentIR:
    document_title: str | None = None
    template_family: str | None = None
    source_kinds: list[InputKind] = field(default_factory=list)
    sections: list[DocumentSectionPlan] = field(default_factory=list)
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)
    references: list[dict[str, str]] = field(default_factory=list)
    figures: list[dict[str, str | int]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "document_title": self.document_title,
            "template_family": self.template_family,
            "source_kinds": list(self.source_kinds),
            "sections": [section.to_dict() for section in self.sections],
            "metadata": dict(self.metadata),
            "references": list(self.references),
            "figures": list(self.figures),
        }
