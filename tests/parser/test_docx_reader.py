import unittest
from io import BytesIO
from zipfile import ZipFile

from md2word_agent.parser import DocxReader, TemplateFileParser
from md2word_agent.specs import TemplateRequirement, TemplateSectionRequirement

CONTENT_TYPES_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

DOCUMENT_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>I. INTRODUCTION</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>II. Guidelines For Manuscript Preparation</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Normal"/></w:pPr>
      <w:r><w:t>This section explains writing guidance for authors.</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
      <w:r><w:t>A. Method</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>References</w:t></w:r>
    </w:p>
  </w:body>
</w:document>'''

STYLES_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="Heading 1"/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="Heading 2"/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>
</w:styles>'''


def build_minimal_docx() -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        archive.writestr("word/document.xml", DOCUMENT_XML)
        archive.writestr("word/styles.xml", STYLES_XML)
    return buffer.getvalue()


class FakePlanner:
    def build_requirement(self, *, candidates, document_family, rule_text=None):
        requirement = TemplateRequirement(document_family=document_family, source_kinds=["template_file"])
        for candidate in candidates:
            title = candidate.title
            if "guidelines" in title.lower():
                continue
            normalized = title
            if title == "I. INTRODUCTION":
                normalized = "Introduction"
            elif title == "A. Method":
                normalized = "Method"
            requirement.required_sections.append(
                TemplateSectionRequirement(
                    title=normalized,
                    level=candidate.level,
                    required=True,
                    section_type=(normalized.lower() if normalized != "Introduction" else "introduction"),
                    notes=["classified by fake planner"],
                )
            )
        requirement.citation_style = "numeric_or_template_defined"
        return requirement


class DocxReaderTests(unittest.TestCase):
    def test_reads_paragraphs_and_styles(self) -> None:
        reader = DocxReader()
        record = reader.read(build_minimal_docx())
        self.assertEqual(len(record.paragraphs), 5)
        self.assertEqual(record.paragraphs[0].text, "I. INTRODUCTION")
        self.assertEqual(record.paragraphs[0].style_name, "Heading 1")
        self.assertIn("Heading1", record.styles)

    def test_template_file_parser_extracts_candidates_and_uses_planner(self) -> None:
        parser = TemplateFileParser(understanding_planner=FakePlanner())
        result = parser.parse(build_minimal_docx(), document_family="ieee_cs")
        candidate_titles = [candidate.title for candidate in result.candidates]
        self.assertIn("II. Guidelines For Manuscript Preparation", candidate_titles)
        titles = [section.title for section in result.requirement.required_sections]
        self.assertIn("Introduction", titles)
        self.assertIn("Method", titles)
        self.assertIn("References", titles)
        self.assertNotIn("II. Guidelines For Manuscript Preparation", titles)
        self.assertEqual(result.requirement.citation_style, "numeric_or_template_defined")


if __name__ == "__main__":
    unittest.main()
