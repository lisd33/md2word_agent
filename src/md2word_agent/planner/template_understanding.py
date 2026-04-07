from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
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
    def __init__(self, client: JSONGenerator, output_dir: str | Path | None = None) -> None:
        self.client = client
        self.output_dir = Path(output_dir) if output_dir else self._default_output_dir()

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
        requirement = self._to_requirement(response, document_family)
        self._persist_run(
            document_family=document_family,
            payload=payload,
            response=response,
            requirement=requirement,
        )
        return requirement

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

    def _persist_run(
        self,
        *,
        document_family: str,
        payload: dict,
        response: dict,
        requirement: TemplateRequirement,
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        target = self.output_dir / f"{timestamp}_{document_family}_template_understanding.json"
        artifact = {
            "saved_at_utc": datetime.now(UTC).isoformat(),
            "document_family": document_family,
            "client_class": self.client.__class__.__name__,
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt_payload": payload,
            "model_response": response,
            "normalized_requirement": requirement.to_dict(),
        }
        target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    def _default_output_dir(self) -> Path:
        return Path(__file__).resolve().parents[3] / "intermediate_outputs" / "template_understanding"
