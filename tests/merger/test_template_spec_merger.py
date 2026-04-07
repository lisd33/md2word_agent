import unittest

from md2word_agent.merger import TemplateSpecMerger
from md2word_agent.specs import TemplateRequirement, TemplateSectionRequirement


class TemplateSpecMergerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.merger = TemplateSpecMerger()

    def test_rule_constraints_override_conflicting_file_values(self) -> None:
        rule_requirement = TemplateRequirement(
            document_family="ieee_cs",
            source_kinds=["rule_text"],
            citation_style="IEEE",
            formatting_constraints={"body_font_family": "Times New Roman"},
        )
        file_requirement = TemplateRequirement(
            document_family="ieee_cs",
            source_kinds=["template_file"],
            citation_style="ACM",
            formatting_constraints={"body_font_family": "Arial"},
        )

        result = self.merger.merge(
            rule_requirement=rule_requirement,
            file_requirement=file_requirement,
        )

        self.assertEqual(result.requirement.citation_style, "IEEE")
        self.assertEqual(result.requirement.formatting_constraints["body_font_family"], "Times New Roman")
        self.assertEqual([conflict.field for conflict in result.conflicts], ["citation_style", "formatting_constraints.body_font_family"])

    def test_file_structure_is_preferred_while_required_wins(self) -> None:
        rule_requirement = TemplateRequirement(
            document_family="ieee_cs",
            source_kinds=["rule_text"],
            required_sections=[
                TemplateSectionRequirement(
                    title="Method",
                    level=1,
                    required=True,
                    section_type="method",
                    notes=["extracted from rule text"],
                )
            ],
        )
        file_requirement = TemplateRequirement(
            document_family="ieee_cs",
            source_kinds=["template_file"],
            optional_sections=[
                TemplateSectionRequirement(
                    title="Methods",
                    level=2,
                    required=False,
                    section_type="method",
                    notes=["kept by semantic understanding"],
                )
            ],
        )

        result = self.merger.merge(
            rule_requirement=rule_requirement,
            file_requirement=file_requirement,
        )

        self.assertEqual(len(result.requirement.required_sections), 1)
        merged_section = result.requirement.required_sections[0]
        self.assertEqual(merged_section.title, "Methods")
        self.assertEqual(merged_section.level, 2)
        self.assertTrue(merged_section.required)
        self.assertEqual(
            [conflict.field for conflict in result.conflicts],
            ["sections.method.required", "sections.method.title", "sections.method.level"],
        )

    def test_rule_only_and_file_only_sections_are_kept_by_union(self) -> None:
        rule_requirement = TemplateRequirement(
            document_family="ieee_cs",
            source_kinds=["rule_text"],
            required_sections=[
                TemplateSectionRequirement(title="Abstract", level=1, required=True, section_type="abstract")
            ],
        )
        file_requirement = TemplateRequirement(
            document_family="ieee_cs",
            source_kinds=["template_file"],
            required_sections=[
                TemplateSectionRequirement(title="Introduction", level=1, required=True, section_type="introduction")
            ],
        )

        result = self.merger.merge(
            rule_requirement=rule_requirement,
            file_requirement=file_requirement,
        )

        self.assertEqual(
            [section.title for section in result.requirement.required_sections],
            ["Introduction", "Abstract"],
        )
        self.assertEqual(result.requirement.source_kinds, ["template_file", "rule_text"])


if __name__ == "__main__":
    unittest.main()
