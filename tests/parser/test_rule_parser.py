import unittest

from md2word_agent.parser import RuleParser


class RuleParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = RuleParser()

    def test_extracts_citation_style_and_required_sections(self) -> None:
        text = (
            "The paper must include Abstract, Introduction, Method, Conclusion, and References. "
            "Use IEEE citation format."
        )
        result = self.parser.parse(text, document_family="ieee_cs")
        requirement = result.requirement
        self.assertEqual(requirement.citation_style, "IEEE")
        titles = [section.title for section in requirement.required_sections]
        self.assertIn("Abstract", titles)
        self.assertIn("Introduction", titles)
        self.assertIn("Method", titles)
        self.assertIn("Conclusion", titles)
        self.assertIn("References", titles)

    def test_extracts_basic_formatting_constraints(self) -> None:
        text = (
            "Title font is Times New Roman. "
            "Title font size is 14pt. "
            "Body font is Times New Roman. "
            "Body font size is 10pt. "
            "Line spacing is 20pt."
        )
        result = self.parser.parse(text)
        constraints = result.requirement.formatting_constraints
        self.assertEqual(constraints["title_font_family"], "Times New Roman")
        self.assertEqual(constraints["title_font_size"], "14pt")
        self.assertEqual(constraints["body_font_family"], "Times New Roman")
        self.assertEqual(constraints["body_font_size"], "10pt")
        self.assertEqual(constraints["body_line_spacing"], "20pt")

    def test_extracts_optional_sections(self) -> None:
        text = "Optional sections: Related Work, Discussion"
        result = self.parser.parse(text)
        titles = [section.title for section in result.requirement.optional_sections]
        self.assertEqual(titles, ["Related Work", "Discussion"])


if __name__ == "__main__":
    unittest.main()
