import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from md2word_agent.api import ParseAPIService


class FakeClient:
    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "required_sections": [
                {
                    "title": "Introduction",
                    "level": 1,
                    "required": True,
                    "section_type": "introduction",
                    "notes": ["kept by fake api test"],
                }
            ],
            "optional_sections": [],
            "citation_style": "IEEE",
            "notes": ["fake planner response"],
        }


class ConflictingFakeClient:
    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "required_sections": [
                {
                    "title": "Methods",
                    "level": 2,
                    "required": False,
                    "section_type": "method",
                    "notes": ["kept by conflicting fake api test"],
                }
            ],
            "optional_sections": [],
            "citation_style": "ACM",
            "notes": ["conflicting fake planner response"],
        }


def build_test_docx_bytes() -> bytes:
    content_types = """<?xml version='1.0' encoding='UTF-8'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
  <Default Extension='xml' ContentType='application/xml'/>
  <Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/>
  <Override PartName='/word/styles.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml'/>
</Types>
"""
    document_xml = """<?xml version='1.0' encoding='UTF-8'?>
<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val='Heading1'/></w:pPr>
      <w:r><w:t>I. INTRODUCTION</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Intro body.</w:t></w:r>
    </w:p>
  </w:body>
</w:document>
"""
    styles_xml = """<?xml version='1.0' encoding='UTF-8'?>
<w:styles xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
  <w:style w:type='paragraph' w:styleId='Heading1'>
    <w:name w:val='Heading 1'/>
  </w:style>
</w:styles>
"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('word/document.xml', document_xml)
        zf.writestr('word/styles.xml', styles_xml)
    return buffer.getvalue()


class ParseAPIServiceTests(unittest.TestCase):
    def test_parse_rule_text(self) -> None:
        service = ParseAPIService()
        payload = service.parse_rule_text(
            text='The paper must include Abstract, Introduction, Method, Conclusion, and References. Use IEEE citation style.',
            document_family='ieee_cs',
        )
        self.assertEqual(payload['document_family'], 'ieee_cs')
        self.assertEqual(payload['requirement']['citation_style'], 'IEEE')
        self.assertIn('evidence', payload)

    def test_parse_docx_template_from_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = Path(tmpdir) / 'sample.docx'
            docx_path.write_bytes(build_test_docx_bytes())

            def fake_factory(*, env_path=None, provider=None):
                return FakeClient()

            service = ParseAPIService(env_file='ignored.env', client_factory=fake_factory)
            payload = service.parse_docx_template(
                document_family='ieee_cs',
                provider='zhipu',
                docx_path=str(docx_path),
            )
            self.assertEqual(payload['provider'], 'zhipu')
            self.assertEqual(payload['requirement']['citation_style'], 'IEEE')
            self.assertEqual(payload['requirement']['required_sections'][0]['title'], 'Introduction')
            self.assertEqual(payload['candidates'][0]['title'], 'I. INTRODUCTION')

    def test_parse_merged_template_spec_from_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = Path(tmpdir) / 'sample.docx'
            docx_path.write_bytes(build_test_docx_bytes())

            def fake_factory(*, env_path=None, provider=None):
                return ConflictingFakeClient()

            service = ParseAPIService(env_file='ignored.env', client_factory=fake_factory)
            payload = service.parse_merged_template_spec(
                document_family='ieee_cs',
                provider='zhipu',
                docx_path=str(docx_path),
                rule_text='The paper must include Method and References. Use IEEE citation style.',
            )
            self.assertEqual(payload['provider'], 'zhipu')
            self.assertEqual(payload['requirement']['citation_style'], 'IEEE')
            self.assertEqual(payload['requirement']['required_sections'][0]['title'], 'Methods')
            self.assertIn('rule_requirement', payload)
            self.assertIn('file_requirement', payload)
            self.assertIn('rule_evidence', payload)
            self.assertIn('candidates', payload)
            self.assertEqual(payload['conflicts'][0]['field'], 'citation_style')


if __name__ == '__main__':
    unittest.main()
