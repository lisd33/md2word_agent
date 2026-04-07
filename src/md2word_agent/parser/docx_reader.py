from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from .models import DocxDocumentRecord, ParagraphRecord, StyleRecord

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


class DocxReader:
    """Minimal OOXML reader for extracting paragraphs and style references from docx files."""

    def read(self, data: bytes) -> DocxDocumentRecord:
        with ZipFile(BytesIO(data)) as archive:
            document_xml = archive.read("word/document.xml")
            styles_xml = archive.read("word/styles.xml") if "word/styles.xml" in archive.namelist() else None

        styles = self._read_styles(styles_xml) if styles_xml else {}
        paragraphs = self._read_paragraphs(document_xml, styles)
        return DocxDocumentRecord(paragraphs=paragraphs, styles=styles)

    def _read_styles(self, xml_bytes: bytes) -> dict[str, StyleRecord]:
        root = ET.fromstring(xml_bytes)
        styles: dict[str, StyleRecord] = {}
        for style in root.findall("w:style", NS):
            style_id = style.attrib.get(f"{{{W_NS}}}styleId")
            if not style_id:
                continue
            name_el = style.find("w:name", NS)
            based_on_el = style.find("w:basedOn", NS)
            styles[style_id] = StyleRecord(
                style_id=style_id,
                style_name=(name_el.attrib.get(f"{{{W_NS}}}val") if name_el is not None else None),
                based_on=(based_on_el.attrib.get(f"{{{W_NS}}}val") if based_on_el is not None else None),
            )
        return styles

    def _read_paragraphs(
        self, xml_bytes: bytes, styles: dict[str, StyleRecord]
    ) -> list[ParagraphRecord]:
        root = ET.fromstring(xml_bytes)
        paragraphs: list[ParagraphRecord] = []
        for paragraph in root.findall(".//w:body/w:p", NS):
            texts = []
            for text_el in paragraph.findall(".//w:t", NS):
                if text_el.text:
                    texts.append(text_el.text)
            text = "".join(texts).strip()
            ppr = paragraph.find("w:pPr", NS)
            style_id = None
            numbering_level = None
            if ppr is not None:
                p_style = ppr.find("w:pStyle", NS)
                if p_style is not None:
                    style_id = p_style.attrib.get(f"{{{W_NS}}}val")
                ilvl = ppr.find("w:numPr/w:ilvl", NS)
                if ilvl is not None:
                    val = ilvl.attrib.get(f"{{{W_NS}}}val")
                    numbering_level = int(val) if val is not None and val.isdigit() else None
            style_name = styles.get(style_id).style_name if style_id in styles else None
            paragraphs.append(
                ParagraphRecord(
                    text=text,
                    style_id=style_id,
                    style_name=style_name,
                    numbering_level=numbering_level,
                )
            )
        return paragraphs
