from __future__ import annotations

import re
from dataclasses import dataclass, field

from md2word_agent.specs import TemplateRequirement, TemplateSectionRequirement

SECTION_PATTERNS = {
    "abstract": [r"\babstract\b", r"摘要"],
    "introduction": [r"\bintroduction\b", r"引言"],
    "related_work": [r"related work", r"相关工作"],
    "method": [r"\bmethod(?:ology)?\b", r"方法"],
    "experiments": [r"\bexperiments?\b", r"实验"],
    "results": [r"\bresults?\b", r"结果"],
    "discussion": [r"\bdiscussion\b", r"讨论"],
    "conclusion": [r"\bconclusion\b", r"结论"],
    "references": [r"\breferences\b", r"参考文献"],
}

SECTION_TITLES = {
    "abstract": "Abstract",
    "introduction": "Introduction",
    "related_work": "Related Work",
    "method": "Method",
    "experiments": "Experiments",
    "results": "Results",
    "discussion": "Discussion",
    "conclusion": "Conclusion",
    "references": "References",
}

CITATION_PATTERNS = [
    ("IEEE", [r"\bieee\b", r"numeric citation", r"数字引用"]),
    ("ACM", [r"\bacm\b"]),
    ("Springer", [r"\bspringer\b"]),
    ("APA", [r"\bapa\b", r"author[- ]year"]),
]

FONT_FAMILY_PATTERNS = [
    r"(?P<label>title|heading|正文|标题|body)\s+font(?!\s+size)\s+(?:is\s+)?(?P<value>[A-Za-z][A-Za-z0-9\- ]+)\.",
    r"(?P<label>title|heading|正文|标题|body)\s*字体\s*(?:为|是|:)?\s*(?P<value>[A-Za-z0-9\u4e00-\u9fff\- ]+)",
]

FONT_SIZE_PATTERNS = [
    r"(?P<label>title|heading|正文|标题|body)\s+font size\s*(?:is|:)?\s*(?P<value>[0-9]+(?:\.[0-9]+)?\s*(?:pt|磅))",
    r"(?P<label>title|heading|正文|标题|body)\s*字号\s*(?:为|是|:)?\s*(?P<value>[0-9]+(?:\.[0-9]+)?\s*(?:pt|磅)|[小一二三四五六七八九十]+)",
]

LINE_SPACING_PATTERNS = [
    r"(?:line spacing|行距)\s*(?:is|为|:)?\s*(?P<value>[0-9]+(?:\.[0-9]+)?\s*(?:pt|磅|倍))",
]

REQUIRED_SECTION_PATTERNS = [
    r"must include (?P<section_list>[A-Za-z, ]+?(?:\sand\s[A-Za-z ]+)?)\.",
    r"include sections? such as (?P<section_list>[A-Za-z, ]+?(?:\sand\s[A-Za-z ]+)?)\.",
    r"应包含(?P<section_zh>[\u4e00-\u9fff、，]+)",
]

OPTIONAL_SECTION_PATTERNS = [
    r"optional sections?: (?P<section_list>[A-Za-z, ]+?(?:\sand\s[A-Za-z ]+)?)\.?$",
    r"可选章节(?:包括|有)?(?P<section_zh>[\u4e00-\u9fff、，]+)",
]


@dataclass(slots=True)
class RuleParseResult:
    requirement: TemplateRequirement
    evidence: dict[str, list[str]] = field(default_factory=dict)


class RuleParser:
    """Lightweight extractor from natural-language template rules to TemplateRequirement."""

    def parse(self, text: str, *, document_family: str = "unknown") -> RuleParseResult:
        lowered = text.lower()
        evidence: dict[str, list[str]] = {}
        requirement = TemplateRequirement(
            document_family=document_family,
            source_kinds=["rule_text"],
        )

        citation_style = self._extract_citation_style(lowered, evidence)
        if citation_style:
            requirement.citation_style = citation_style

        formatting_constraints = self._extract_formatting_constraints(text, evidence)
        if formatting_constraints:
            requirement.formatting_constraints.update(formatting_constraints)

        required_sections = self._extract_sections(text, lowered, evidence, required=True)
        optional_sections = self._extract_sections(text, lowered, evidence, required=False)
        requirement.required_sections.extend(required_sections)
        requirement.optional_sections.extend(optional_sections)

        if not requirement.required_sections:
            inferred_sections = self._infer_sections_from_mentions(lowered, evidence)
            requirement.required_sections.extend(inferred_sections)

        if not any(
            [
                requirement.citation_style,
                requirement.formatting_constraints,
                requirement.required_sections,
                requirement.optional_sections,
            ]
        ):
            requirement.notes.append("No explicit constraints were extracted from rule text.")

        return RuleParseResult(requirement=requirement, evidence=evidence)

    def _extract_citation_style(self, lowered: str, evidence: dict[str, list[str]]) -> str | None:
        for style, patterns in CITATION_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, lowered):
                    evidence.setdefault("citation_style", []).append(pattern)
                    return style
        return None

    def _extract_formatting_constraints(self, text: str, evidence: dict[str, list[str]]) -> dict[str, str]:
        constraints: dict[str, str] = {}
        for pattern in FONT_FAMILY_PATTERNS:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                label = self._normalize_label(match.group("label"))
                value = match.group("value").strip().rstrip(".,;")
                constraints[f"{label}_font_family"] = value
                evidence.setdefault("formatting_constraints", []).append(match.group(0))
        for pattern in FONT_SIZE_PATTERNS:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                label = self._normalize_label(match.group("label"))
                value = match.group("value").strip().rstrip(".,;")
                constraints[f"{label}_font_size"] = value
                evidence.setdefault("formatting_constraints", []).append(match.group(0))
        for pattern in LINE_SPACING_PATTERNS:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = match.group("value").strip().rstrip(".,;")
                constraints["body_line_spacing"] = value
                evidence.setdefault("formatting_constraints", []).append(match.group(0))
        return constraints

    def _extract_sections(
        self,
        text: str,
        lowered: str,
        evidence: dict[str, list[str]],
        *,
        required: bool,
    ) -> list[TemplateSectionRequirement]:
        patterns = REQUIRED_SECTION_PATTERNS if required else OPTIONAL_SECTION_PATTERNS
        found: list[TemplateSectionRequirement] = []
        seen_titles: set[str] = set()
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                captured = (
                    match.groupdict().get("section_list")
                    or match.groupdict().get("section_zh")
                    or ""
                )
                if not captured:
                    continue
                for chunk in self._split_section_candidates(captured):
                    normalized = self._normalize_section_name(chunk)
                    if not normalized or normalized in seen_titles:
                        continue
                    found.append(
                        TemplateSectionRequirement(
                            title=normalized,
                            level=1,
                            required=required,
                            section_type=self._infer_section_type(normalized),
                            notes=["extracted from rule text"],
                        )
                    )
                    evidence.setdefault(
                        "required_sections" if required else "optional_sections", []
                    ).append(match.group(0))
                    seen_titles.add(normalized)
        if found:
            return found

        mentioned: list[TemplateSectionRequirement] = []
        for key, patterns_for_key in SECTION_PATTERNS.items():
            if any(re.search(pattern, lowered) for pattern in patterns_for_key):
                title = SECTION_TITLES[key]
                if title in seen_titles:
                    continue
                if required and key in {"abstract", "introduction", "conclusion", "references"}:
                    mentioned.append(
                        TemplateSectionRequirement(
                            title=title,
                            level=1,
                            required=True,
                            section_type=key,
                            notes=["inferred from strong rule-text mention"],
                        )
                    )
                    seen_titles.add(title)
                elif not required and key not in {"abstract", "introduction", "conclusion", "references"}:
                    mentioned.append(
                        TemplateSectionRequirement(
                            title=title,
                            level=1,
                            required=False,
                            section_type=key,
                            notes=["inferred from weak rule-text mention"],
                        )
                    )
                    seen_titles.add(title)
        if mentioned:
            evidence.setdefault(
                "required_sections" if required else "optional_sections", []
            ).append("inferred from section mentions")
        return mentioned

    def _infer_sections_from_mentions(
        self, lowered: str, evidence: dict[str, list[str]]
    ) -> list[TemplateSectionRequirement]:
        inferred: list[TemplateSectionRequirement] = []
        for key in ["abstract", "introduction", "conclusion", "references"]:
            if any(re.search(pattern, lowered) for pattern in SECTION_PATTERNS[key]):
                inferred.append(
                    TemplateSectionRequirement(
                        title=SECTION_TITLES[key],
                        level=1,
                        required=True,
                        section_type=key,
                        notes=["fallback inference from rule text"],
                    )
                )
        if inferred:
            evidence.setdefault("required_sections", []).append("fallback section inference")
        return inferred

    def _split_section_candidates(self, captured: str) -> list[str]:
        normalized = re.sub(r"\band\b", ",", captured, flags=re.IGNORECASE)
        return [chunk.strip() for chunk in re.split(r"[,，、]", normalized) if chunk.strip()]

    def _normalize_label(self, label: str) -> str:
        mapping = {
            "title": "title",
            "heading": "heading",
            "标题": "heading",
            "正文": "body",
            "body": "body",
        }
        return mapping.get(label.lower(), label.lower())

    def _normalize_section_name(self, name: str) -> str | None:
        cleaned = name.strip().strip(".:")
        if not cleaned:
            return None
        lowered = cleaned.lower()
        for key, patterns in SECTION_PATTERNS.items():
            if any(re.search(pattern, lowered) for pattern in patterns):
                return SECTION_TITLES[key]
        if cleaned:
            return cleaned.title()
        return None

    def _infer_section_type(self, title: str) -> str | None:
        lowered = title.lower()
        for key, normalized in SECTION_TITLES.items():
            if normalized.lower() == lowered:
                return key
        return None
