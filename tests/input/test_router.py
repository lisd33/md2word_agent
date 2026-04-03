import unittest

from md2word_agent.input import InputPayload, InputRouter


class InputRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = InputRouter()

    def test_routes_docx_as_template_file(self) -> None:
        routed = self.router.route_payload(
            InputPayload(name="ieee-template", path="template.docx")
        )
        self.assertEqual(routed.kind, "template_file")

    def test_routes_rule_text_via_keywords(self) -> None:
        routed = self.router.route_payload(
            InputPayload(
                name="author-guidelines",
                text="Title font size should be 14pt and line spacing should be 20pt.",
            )
        )
        self.assertEqual(routed.kind, "rule_text")

    def test_routes_content_draft_via_semantic_keywords(self) -> None:
        routed = self.router.route_payload(
            InputPayload(
                name="draft",
                text="Abstract: This paper proposes a new method and concludes with experiments.",
            )
        )
        self.assertEqual(routed.kind, "content_draft")

    def test_batch_becomes_mixed_when_sources_differ(self) -> None:
        routed = self.router.route_batch(
            [
                InputPayload(name="template", path="paper.docx"),
                InputPayload(name="guide", text="Use IEEE citation format and 10pt font."),
            ]
        )
        self.assertTrue(all(item.kind == "mixed_input" for item in routed))


if __name__ == "__main__":
    unittest.main()
