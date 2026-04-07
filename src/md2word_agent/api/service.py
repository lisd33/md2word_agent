from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

from md2word_agent.llm import create_json_client, resolve_provider
from md2word_agent.merger import TemplateSpecMerger
from md2word_agent.parser import RuleParser, TemplateFileParser
from md2word_agent.planner import TemplateUnderstandingPlanner


ClientFactory = Callable[..., Any]


@dataclass(slots=True)
class ParseAPIService:
    env_file: str | Path | None = None
    client_factory: ClientFactory = create_json_client

    def parse_rule_text(
        self,
        *,
        text: str,
        document_family: str = "unknown",
        include_evidence: bool = True,
    ) -> dict:
        result = RuleParser().parse(text, document_family=document_family)
        payload = {
            "document_family": document_family,
            "requirement": result.requirement.to_dict(),
        }
        if include_evidence:
            payload["evidence"] = result.evidence
        return payload

    def parse_docx_template(
        self,
        *,
        document_family: str = "unknown",
        provider: str | None = None,
        docx_path: str | None = None,
        docx_base64: str | None = None,
        rule_text: str | None = None,
        include_candidates: bool = True,
    ) -> dict:
        data = self._load_docx_bytes(docx_path=docx_path, docx_base64=docx_base64)
        selected_provider = resolve_provider(self.env_file, provider)
        client = self.client_factory(env_path=self.env_file, provider=selected_provider)
        planner = TemplateUnderstandingPlanner(client)
        parser = TemplateFileParser(understanding_planner=planner)
        result = parser.parse(data, document_family=document_family, rule_text=rule_text)
        payload = {
            "provider": selected_provider,
            "document_family": document_family,
            "requirement": result.requirement.to_dict(),
        }
        if include_candidates:
            payload["candidates"] = [candidate.to_dict() for candidate in result.candidates]
        return payload

    def parse_merged_template_spec(
        self,
        *,
        document_family: str = "unknown",
        provider: str | None = None,
        docx_path: str | None = None,
        docx_base64: str | None = None,
        rule_text: str,
        include_candidates: bool = True,
        include_evidence: bool = True,
    ) -> dict:
        data = self._load_docx_bytes(docx_path=docx_path, docx_base64=docx_base64)
        selected_provider = resolve_provider(self.env_file, provider)
        client = self.client_factory(env_path=self.env_file, provider=selected_provider)
        planner = TemplateUnderstandingPlanner(client)
        parser = TemplateFileParser(understanding_planner=planner)

        rule_result = RuleParser().parse(rule_text, document_family=document_family)
        file_result = parser.parse(data, document_family=document_family, rule_text=rule_text)
        merge_result = TemplateSpecMerger().merge(
            rule_requirement=rule_result.requirement,
            file_requirement=file_result.requirement,
        )

        payload = {
            "provider": selected_provider,
            "document_family": document_family,
            "requirement": merge_result.requirement.to_dict(),
            "rule_requirement": rule_result.requirement.to_dict(),
            "file_requirement": file_result.requirement.to_dict(),
            "conflicts": [conflict.to_dict() for conflict in merge_result.conflicts],
            "precedence_rules": list(merge_result.precedence_rules),
        }
        if include_candidates:
            payload["candidates"] = [candidate.to_dict() for candidate in file_result.candidates]
        if include_evidence:
            payload["rule_evidence"] = rule_result.evidence
        return payload

    def _load_docx_bytes(self, *, docx_path: str | None, docx_base64: str | None) -> bytes:
        if docx_path and docx_base64:
            raise ValueError("Provide either docx_path or docx_base64, not both.")
        if docx_path:
            return Path(docx_path).read_bytes()
        if docx_base64:
            return base64.b64decode(docx_base64)
        raise ValueError("One of docx_path or docx_base64 is required.")
