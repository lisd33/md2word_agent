from __future__ import annotations

from dataclasses import dataclass, field

from md2word_agent.specs import TemplateRequirement, TemplateSectionRequirement


CANONICAL_SECTION_ALIASES = {
    "acknowledgement": "acknowledgment",
    "acknowledgements": "acknowledgment",
    "conclusions": "conclusion",
    "experiment": "experiments",
    "methodology": "method",
    "methods": "method",
    "reference": "references",
    "result": "results",
}


@dataclass(slots=True)
class MergeConflict:
    field: str
    resolution: str
    rule_value: str | int | float | bool | None = None
    file_value: str | int | float | bool | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "resolution": self.resolution,
            "rule_value": self.rule_value,
            "file_value": self.file_value,
            "notes": list(self.notes),
        }


@dataclass(slots=True)
class TemplateSpecMergeResult:
    requirement: TemplateRequirement
    conflicts: list[MergeConflict] = field(default_factory=list)
    precedence_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "requirement": self.requirement.to_dict(),
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "precedence_rules": list(self.precedence_rules),
        }


class TemplateSpecMerger:
    """Merge rule-derived and file-derived template requirements."""

    PRECEDENCE_RULES = [
        "Explicit rule-text constraints override conflicting file-derived formatting and citation values.",
        "File-derived structure is preferred for section title, level, and section type when both sources refer to the same section.",
        "Section presence is merged by union, and required wins over optional to preserve stricter template constraints.",
        "Conflicting values are preserved as merge diagnostics instead of being silently discarded.",
    ]

    def merge(
        self,
        *,
        rule_requirement: TemplateRequirement,
        file_requirement: TemplateRequirement,
    ) -> TemplateSpecMergeResult:
        document_family = self._pick_document_family(rule_requirement, file_requirement)
        merged = TemplateRequirement(
            document_family=document_family,
            source_kinds=self._merge_source_kinds(rule_requirement, file_requirement),
        )
        conflicts: list[MergeConflict] = []

        merged.citation_style = self._merge_scalar(
            field_name="citation_style",
            rule_value=rule_requirement.citation_style,
            file_value=file_requirement.citation_style,
            conflicts=conflicts,
            prefer="rule",
        )
        merged.formatting_constraints = self._merge_constraints(
            rule_constraints=rule_requirement.formatting_constraints,
            file_constraints=file_requirement.formatting_constraints,
            conflicts=conflicts,
        )
        merged.figure_requirements = self._merge_constraints(
            rule_constraints=rule_requirement.figure_requirements,
            file_constraints=file_requirement.figure_requirements,
            conflicts=conflicts,
            field_prefix="figure_requirements",
            prefer="file",
        )
        required_sections, optional_sections = self._merge_sections(
            rule_requirement=rule_requirement,
            file_requirement=file_requirement,
            conflicts=conflicts,
        )
        merged.required_sections = required_sections
        merged.optional_sections = optional_sections
        merged.notes = self._merge_notes(rule_requirement.notes, file_requirement.notes)
        if conflicts:
            merged.notes.append(f"Merged with {len(conflicts)} conflict(s); see merge diagnostics.")

        return TemplateSpecMergeResult(
            requirement=merged,
            conflicts=conflicts,
            precedence_rules=list(self.PRECEDENCE_RULES),
        )

    def _pick_document_family(
        self,
        rule_requirement: TemplateRequirement,
        file_requirement: TemplateRequirement,
    ) -> str:
        if rule_requirement.document_family != "unknown":
            return rule_requirement.document_family
        return file_requirement.document_family

    def _merge_source_kinds(
        self,
        rule_requirement: TemplateRequirement,
        file_requirement: TemplateRequirement,
    ) -> list[str]:
        merged: list[str] = []
        for source_kind in [*file_requirement.source_kinds, *rule_requirement.source_kinds]:
            if source_kind not in merged:
                merged.append(source_kind)
        return merged

    def _merge_scalar(
        self,
        *,
        field_name: str,
        rule_value: str | int | float | bool | None,
        file_value: str | int | float | bool | None,
        conflicts: list[MergeConflict],
        prefer: str,
    ) -> str | int | float | bool | None:
        if rule_value is None:
            return file_value
        if file_value is None:
            return rule_value
        if rule_value == file_value:
            return rule_value

        resolved_value = rule_value if prefer == "rule" else file_value
        conflicts.append(
            MergeConflict(
                field=field_name,
                rule_value=rule_value,
                file_value=file_value,
                resolution=f"kept {prefer}-derived value",
            )
        )
        return resolved_value

    def _merge_constraints(
        self,
        *,
        rule_constraints: dict[str, str | int | float | bool],
        file_constraints: dict[str, str | int | float | bool],
        conflicts: list[MergeConflict],
        field_prefix: str = "formatting_constraints",
        prefer: str = "rule",
    ) -> dict[str, str | int | float | bool]:
        merged = dict(file_constraints)
        for key, rule_value in rule_constraints.items():
            if key not in merged:
                merged[key] = rule_value
                continue
            file_value = merged[key]
            if file_value == rule_value:
                continue
            merged[key] = rule_value if prefer == "rule" else file_value
            conflicts.append(
                MergeConflict(
                    field=f"{field_prefix}.{key}",
                    rule_value=rule_value,
                    file_value=file_value,
                    resolution=f"kept {prefer}-derived value",
                )
            )
        return merged

    def _merge_sections(
        self,
        *,
        rule_requirement: TemplateRequirement,
        file_requirement: TemplateRequirement,
        conflicts: list[MergeConflict],
    ) -> tuple[list[TemplateSectionRequirement], list[TemplateSectionRequirement]]:
        merged: dict[str, TemplateSectionRequirement] = {}

        for section in file_requirement.required_sections:
            merged[self._section_key(section)] = self._clone_section(section)
        for section in file_requirement.optional_sections:
            merged[self._section_key(section)] = self._clone_section(section, required=False)

        for section in [*rule_requirement.required_sections, *rule_requirement.optional_sections]:
            key = self._section_key(section)
            normalized_rule_section = self._clone_section(section, required=section.required)
            existing_section = merged.get(key)
            if existing_section is None:
                merged[key] = normalized_rule_section
                continue
            merged[key] = self._merge_section_pair(
                key=key,
                rule_section=normalized_rule_section,
                file_section=existing_section,
                conflicts=conflicts,
            )

        required_sections: list[TemplateSectionRequirement] = []
        optional_sections: list[TemplateSectionRequirement] = []
        for section in merged.values():
            if section.required:
                required_sections.append(section)
            else:
                optional_sections.append(section)
        return required_sections, optional_sections

    def _merge_section_pair(
        self,
        *,
        key: str,
        rule_section: TemplateSectionRequirement,
        file_section: TemplateSectionRequirement,
        conflicts: list[MergeConflict],
    ) -> TemplateSectionRequirement:
        required = file_section.required or rule_section.required
        if file_section.required != rule_section.required:
            conflicts.append(
                MergeConflict(
                    field=f"sections.{key}.required",
                    rule_value=rule_section.required,
                    file_value=file_section.required,
                    resolution="kept required=True because stricter constraint wins",
                )
            )

        title = file_section.title
        if file_section.title != rule_section.title:
            conflicts.append(
                MergeConflict(
                    field=f"sections.{key}.title",
                    rule_value=rule_section.title,
                    file_value=file_section.title,
                    resolution="kept file-derived title",
                    notes=["file-derived structure is treated as the better section-title signal"],
                )
            )

        level = file_section.level
        if file_section.level != rule_section.level:
            conflicts.append(
                MergeConflict(
                    field=f"sections.{key}.level",
                    rule_value=rule_section.level,
                    file_value=file_section.level,
                    resolution="kept file-derived level",
                    notes=["file-derived structure is treated as the better hierarchy signal"],
                )
            )

        section_type = file_section.section_type or rule_section.section_type
        if (
            file_section.section_type
            and rule_section.section_type
            and file_section.section_type != rule_section.section_type
        ):
            conflicts.append(
                MergeConflict(
                    field=f"sections.{key}.section_type",
                    rule_value=rule_section.section_type,
                    file_value=file_section.section_type,
                    resolution="kept file-derived section type",
                )
            )

        notes = self._merge_notes(rule_section.notes, file_section.notes)
        return TemplateSectionRequirement(
            title=title,
            level=level,
            required=required,
            section_type=section_type,
            notes=notes,
        )

    def _section_key(self, section: TemplateSectionRequirement) -> str:
        if section.section_type:
            return section.section_type.strip().lower()
        return self._normalize_title_key(section.title)

    def _normalize_title_key(self, title: str) -> str:
        normalized = " ".join(title.strip().lower().replace("-", " ").split())
        return CANONICAL_SECTION_ALIASES.get(normalized, normalized)

    def _clone_section(
        self,
        section: TemplateSectionRequirement,
        *,
        required: bool | None = None,
    ) -> TemplateSectionRequirement:
        return TemplateSectionRequirement(
            title=section.title,
            level=section.level,
            required=section.required if required is None else required,
            section_type=section.section_type,
            notes=list(section.notes),
        )

    def _merge_notes(self, rule_notes: list[str], file_notes: list[str]) -> list[str]:
        merged: list[str] = []
        for note in [*file_notes, *rule_notes]:
            if note not in merged:
                merged.append(note)
        return merged
