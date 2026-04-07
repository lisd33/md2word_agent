import json
import tempfile
import unittest
from pathlib import Path

from md2word_agent.parser.models import TemplateCandidate
from md2word_agent.planner import TemplateUnderstandingPlanner


class FakeClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append((system_prompt, user_prompt))
        return self.response


class TemplateUnderstandingPlannerTests(unittest.TestCase):
    def test_build_requirement_from_client_response(self) -> None:
        client = FakeClient(
            {
                "required_sections": [
                    {
                        "title": "Introduction",
                        "level": 1,
                        "required": True,
                        "section_type": "introduction",
                        "notes": ["kept by semantic understanding"],
                    },
                    {
                        "title": "Conclusion",
                        "level": 1,
                        "required": True,
                        "section_type": "conclusion",
                        "notes": ["kept by semantic understanding"],
                    },
                ],
                "optional_sections": [],
                "citation_style": "IEEE",
                "notes": ["instructional sections dropped"],
            }
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            planner = TemplateUnderstandingPlanner(client, output_dir=tmpdir)
            requirement = planner.build_requirement(
                candidates=[
                    TemplateCandidate(
                        title="I. INTRODUCTION",
                        level=1,
                        style_id="Heading1",
                        style_name="Heading 1",
                    ),
                    TemplateCandidate(
                        title="III. MATH",
                        level=1,
                        style_id="Heading1",
                        style_name="Heading 1",
                        next_text="Use either the Microsoft Equation Editor or the MathType plugin.",
                    ),
                    TemplateCandidate(
                        title="V. CONCLUSION",
                        level=1,
                        style_id="Heading1",
                        style_name="Heading 1",
                    ),
                ],
                document_family="ieee_cs",
                rule_text="Use IEEE reference style.",
            )

            self.assertEqual(requirement.document_family, "ieee_cs")
            self.assertEqual(requirement.source_kinds, ["template_file"])
            self.assertEqual(requirement.citation_style, "IEEE")
            self.assertEqual([section.title for section in requirement.required_sections], ["Introduction", "Conclusion"])
            self.assertEqual(requirement.notes, ["instructional sections dropped"])
            self.assertEqual(len(client.calls), 1)
            self.assertIn("III. MATH", client.calls[0][1])

            output_files = list(Path(tmpdir).glob("*.json"))
            self.assertEqual(len(output_files), 1)
            artifact = json.loads(output_files[0].read_text(encoding="utf-8"))
            self.assertEqual(artifact["client_class"], "FakeClient")
            self.assertEqual(artifact["model_response"]["citation_style"], "IEEE")
            self.assertEqual(artifact["normalized_requirement"]["document_family"], "ieee_cs")


if __name__ == "__main__":
    unittest.main()
