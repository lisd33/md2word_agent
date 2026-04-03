import unittest

from md2word_agent.specs import (
    ContentIntent,
    DocumentIR,
    DocumentSectionPlan,
    TemplateRequirement,
    TemplateSectionRequirement,
)


class SpecModelTests(unittest.TestCase):
    def test_template_requirement_serializes(self) -> None:
        requirement = TemplateRequirement(
            document_family="ieee_computer_science",
            source_kinds=["template_file", "rule_text"],
            required_sections=[
                TemplateSectionRequirement(title="Abstract", level=1, section_type="abstract")
            ],
            citation_style="IEEE",
        )
        data = requirement.to_dict()
        self.assertEqual(data["document_family"], "ieee_computer_science")
        self.assertEqual(data["required_sections"][0]["title"], "Abstract")

    def test_content_intent_serializes(self) -> None:
        intent = ContentIntent(
            title="Neural Layout Planning",
            domain="document intelligence",
            paper_type="experimental",
            keywords=["layout", "planning"],
            has_experiments=True,
        )
        data = intent.to_dict()
        self.assertEqual(data["paper_type"], "experimental")
        self.assertTrue(data["has_experiments"])

    def test_document_ir_serializes_nested_sections(self) -> None:
        doc = DocumentIR(
            document_title="Sample",
            sections=[
                DocumentSectionPlan(
                    title="Introduction",
                    level=1,
                    children=[DocumentSectionPlan(title="Motivation", level=2)],
                )
            ],
        )
        data = doc.to_dict()
        self.assertEqual(data["sections"][0]["children"][0]["title"], "Motivation")


if __name__ == "__main__":
    unittest.main()
