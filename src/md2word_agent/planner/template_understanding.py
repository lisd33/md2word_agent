from __future__ import annotations

import json
from typing import Protocol

from md2word_agent.parser.models import TemplateCandidate
from md2word_agent.specs import TemplateRequirement, TemplateSectionRequirement


class JSONGenerator(Protocol):
    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict: ...


SYSTEM_PROMPT = """You are a template-structure understanding model for academic writing.
Your job is to decide which candidate headings belong to the actual paper skeleton and which ones are only author instructions, formatting guidance, submission instructions, metadata, or noise.
Return strict JSON only.
For each kept section, normalize the title to a canonical academic section title when appropriate.
Never keep instructional sections such as writing guidelines, submission instructions, graphics instructions, math formatting instructions, or policy sections unless they are true paper sections.
"""


class TemplateUnderstandingPlanner:
    def __init__(self, client: JSONGenerator) -> None:
        self.client = client

    def build_requirement(
        self,
        *,
        candidates: list[TemplateCandidate],
        document_family: str,
        rule_text: str | None = None,
    ) -> TemplateRequirement:
        payload = {
            "document_family": document_family,
            "rule_text": rule_text,
            "candidates": [candidate.to_dict() for candidate in candidates],
            "target_schema": {
                "required_sections": [
                    {
                        "title": "string",
                        "level": 1,
                        "required": True,
                        "section_type": "string_or_null",
                        "notes": ["string"],
                    }
                ],
                "optional_sections": [],
                "citation_style": "string_or_null",
                "notes": ["string"],
            },
        }
        user_prompt = json.dumps(payload, ensure_ascii=False, indent=2)
        response = self.client.generate_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        return self._to_requirement(response, document_family)

    def _to_requirement(self, data: dict, document_family: str) -> TemplateRequirement:
        requirement = TemplateRequirement(
            document_family=document_family,
            source_kinds=["template_file"],
            citation_style=data.get("citation_style"),
            notes=list(data.get("notes", [])),
        )
        for item in data.get("required_sections", []):
            requirement.required_sections.append(
                TemplateSectionRequirement(
                    title=item["title"],
                    level=int(item.get("level", 1)),
                    required=bool(item.get("required", True)),
                    section_type=item.get("section_type"),
                    notes=list(item.get("notes", [])),
                )
            )
        for item in data.get("optional_sections", []):
            requirement.optional_sections.append(
                TemplateSectionRequirement(
                    title=item["title"],
                    level=int(item.get("level", 1)),
                    required=bool(item.get("required", False)),
                    section_type=item.get("section_type"),
                    notes=list(item.get("notes", [])),
                )
            )
        return requirement
