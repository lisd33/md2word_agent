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
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
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
    <w:sectPr>
      <w:headerReference w:type="default" r:id="rIdHeader1"/>
      <w:footerReference w:type="default" r:id="rIdFooter1"/>
      <w:titlePg/>
      <w:pgSz w:w="12240" w:h="15840" w:orient="portrait"/>
      <w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080" w:header="720" w:footer="720" w:gutter="0"/>
      <w:cols w:num="2" w:space="720" w:sep="1"/>
    </w:sectPr>
  </w:body>
</w:document>'''

STYLES_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Abstract">
    <w:name w:val="Abstract"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:spacing w:line="360" w:lineRule="atLeast"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="18"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:pPr>
      <w:jc w:val="center"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Cambria" w:hAnsi="Cambria"/>
      <w:sz w:val="28"/>
      <w:b/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="Heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:jc w:val="center"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="24"/>
      <w:b/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="Heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:rPr>
      <w:sz w:val="22"/>
      <w:b/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr>
      <w:spacing w:line="480" w:lineRule="exact"/>
      <w:jc w:val="both"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
      <w:sz w:val="20"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Caption">
    <w:name w:val="Caption"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:jc w:val="center"/>
    </w:pPr>
    <w:rPr>
      <w:i/>
    </w:rPr>
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
    def test_reads_paragraphs_styles_and_layout_constraints(self) -> None:
        reader = DocxReader()
        record = reader.read(build_minimal_docx())
        self.assertEqual(len(record.paragraphs), 5)
        self.assertEqual(record.paragraphs[0].text, "I. INTRODUCTION")
        self.assertEqual(record.paragraphs[0].style_name, "Heading 1")
        self.assertIn("Heading1", record.styles)
        self.assertEqual(record.styles["Normal"].formatting["font_family"], "Times New Roman")
        self.assertEqual(record.styles["Normal"].formatting["font_size"], "10pt")
        self.assertEqual(record.styles["Normal"].formatting["line_spacing"], "24pt")
        self.assertEqual(record.styles["Normal"].formatting["line_spacing_rule"], "exact")
        self.assertEqual(record.styles["Abstract"].formatting["line_spacing"], "18pt")
        self.assertEqual(record.styles["Abstract"].formatting["line_spacing_rule"], "atLeast")
        self.assertEqual(record.styles["Heading1"].formatting["font_family"], "Times New Roman")
        self.assertEqual(record.styles["Heading1"].formatting["font_size"], "12pt")
        self.assertEqual(record.styles["Caption"].formatting["italic"], True)
        self.assertEqual(record.layout_constraints["page_margin_top"], "1.00in")
        self.assertEqual(record.layout_constraints["page_margin_left"], "0.75in")
        self.assertEqual(record.layout_constraints["column_count"], 2)
        self.assertEqual(record.layout_constraints["column_spacing"], "0.50in")
        self.assertEqual(record.layout_constraints["page_orientation"], "portrait")
        self.assertTrue(record.layout_constraints["has_default_header"])
        self.assertTrue(record.layout_constraints["different_first_page_header_footer"])

    def test_template_file_parser_extracts_candidates_and_file_constraints(self) -> None:
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
        self.assertEqual(result.requirement.formatting_constraints["body_font_family"], "Times New Roman")
        self.assertEqual(result.requirement.formatting_constraints["body_font_size"], "10pt")
        self.assertEqual(result.requirement.formatting_constraints["body_line_spacing"], "24pt")
        self.assertEqual(result.requirement.formatting_constraints["body_line_spacing_rule"], "exact")
        self.assertEqual(result.requirement.formatting_constraints["title_font_family"], "Cambria")
        self.assertEqual(result.requirement.formatting_constraints["caption_italic"], True)
        self.assertEqual(result.requirement.formatting_constraints["page_margin_left"], "0.75in")
        self.assertEqual(result.requirement.formatting_constraints["column_count"], 2)
        self.assertEqual(result.requirement.formatting_constraints["column_spacing"], "0.50in")
        self.assertEqual(result.requirement.formatting_constraints["page_orientation"], "portrait")
        self.assertEqual(result.requirement.formatting_constraints["style_abstract_font_size"], "9pt")
        self.assertEqual(result.requirement.formatting_constraints["style_abstract_line_spacing_rule"], "atLeast")
        self.assertEqual(result.requirement.formatting_constraints["style_caption_italic"], True)


if __name__ == "__main__":
    unittest.main()
