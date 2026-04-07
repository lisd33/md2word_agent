from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from .models import DocxDocumentRecord, ParagraphRecord, StyleRecord

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


class DocxReader:
    """OOXML reader for extracting paragraphs, styles, and document layout constraints from docx files."""

    def read(self, data: bytes) -> DocxDocumentRecord:
        with ZipFile(BytesIO(data)) as archive:
            document_xml = archive.read("word/document.xml")
            styles_xml = archive.read("word/styles.xml") if "word/styles.xml" in archive.namelist() else None

        styles = self._read_styles(styles_xml) if styles_xml else {}
        self._resolve_style_formatting(styles)
        paragraphs = self._read_paragraphs(document_xml, styles)
        layout_constraints = self._read_layout_constraints(document_xml)
        return DocxDocumentRecord(
            paragraphs=paragraphs,
            styles=styles,
            layout_constraints=layout_constraints,
        )

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
                style_type=style.attrib.get(f"{{{W_NS}}}type"),
                formatting=self._read_style_formatting(style),
            )
        return styles

    def _read_style_formatting(self, style: ET.Element) -> dict[str, str | int | float | bool]:
        formatting: dict[str, str | int | float | bool] = {}
        ppr = style.find("w:pPr", NS)
        if ppr is not None:
            jc = ppr.find("w:jc", NS)
            spacing = ppr.find("w:spacing", NS)
            if jc is not None:
                alignment = jc.attrib.get(f"{{{W_NS}}}val")
                if alignment:
                    formatting["alignment"] = alignment
            if spacing is not None:
                line = spacing.attrib.get(f"{{{W_NS}}}line")
                line_rule = spacing.attrib.get(f"{{{W_NS}}}lineRule")
                if line:
                    formatting["line_spacing"] = self._format_line_spacing(line, line_rule)
                    formatting["line_spacing_rule"] = line_rule or "auto"

        rpr = style.find("w:rPr", NS)
        if rpr is not None:
            rfonts = rpr.find("w:rFonts", NS)
            if rfonts is not None:
                font_family = (
                    rfonts.attrib.get(f"{{{W_NS}}}ascii")
                    or rfonts.attrib.get(f"{{{W_NS}}}hAnsi")
                    or rfonts.attrib.get(f"{{{W_NS}}}eastAsia")
                    or rfonts.attrib.get(f"{{{W_NS}}}cs")
                )
                if font_family:
                    formatting["font_family"] = font_family

            size = rpr.find("w:sz", NS)
            if size is not None:
                val = size.attrib.get(f"{{{W_NS}}}val")
                if val and val.isdigit():
                    formatting["font_size"] = self._half_points_to_pt_string(val)

            if self._is_enabled(rpr.find("w:b", NS)):
                formatting["bold"] = True
            if self._is_enabled(rpr.find("w:i", NS)):
                formatting["italic"] = True
        return formatting

    def _resolve_style_formatting(self, styles: dict[str, StyleRecord]) -> None:
        resolved_cache: dict[str, dict[str, str | int | float | bool]] = {}

        def resolve(style_id: str) -> dict[str, str | int | float | bool]:
            if style_id in resolved_cache:
                return resolved_cache[style_id]

            style = styles[style_id]
            merged: dict[str, str | int | float | bool] = {}
            if style.based_on and style.based_on in styles and style.based_on != style_id:
                merged.update(resolve(style.based_on))
            merged.update(style.formatting)
            resolved_cache[style_id] = merged
            return merged

        for style_id in styles:
            styles[style_id].formatting = resolve(style_id)

    def _read_layout_constraints(self, xml_bytes: bytes) -> dict[str, str | int | float | bool]:
        root = ET.fromstring(xml_bytes)
        layout: dict[str, str | int | float | bool] = {}
        sect_pr = root.find(".//w:body/w:sectPr", NS)
        if sect_pr is None:
            sect_pr = root.find(".//w:sectPr", NS)
        if sect_pr is None:
            return layout

        pg_sz = sect_pr.find("w:pgSz", NS)
        if pg_sz is not None:
            width = pg_sz.attrib.get(f"{{{W_NS}}}w")
            height = pg_sz.attrib.get(f"{{{W_NS}}}h")
            orient = pg_sz.attrib.get(f"{{{W_NS}}}orient")
            if width:
                layout["page_width"] = self._twips_to_inches_string(width)
            if height:
                layout["page_height"] = self._twips_to_inches_string(height)
            if orient:
                layout["page_orientation"] = orient

        pg_mar = sect_pr.find("w:pgMar", NS)
        if pg_mar is not None:
            for attr, key in {
                "top": "page_margin_top",
                "right": "page_margin_right",
                "bottom": "page_margin_bottom",
                "left": "page_margin_left",
                "header": "header_distance",
                "footer": "footer_distance",
                "gutter": "page_margin_gutter",
            }.items():
                value = pg_mar.attrib.get(f"{{{W_NS}}}{attr}")
                if value is not None:
                    layout[key] = self._twips_to_inches_string(value)

        cols = sect_pr.find("w:cols", NS)
        if cols is not None:
            num = cols.attrib.get(f"{{{W_NS}}}num")
            space = cols.attrib.get(f"{{{W_NS}}}space")
            sep = cols.attrib.get(f"{{{W_NS}}}sep")
            equal_width = cols.attrib.get(f"{{{W_NS}}}equalWidth")
            if num and num.isdigit():
                layout["column_count"] = int(num)
            else:
                layout["column_count"] = 1
            if space is not None:
                layout["column_spacing"] = self._twips_to_inches_string(space)
            if sep is not None:
                layout["column_separator"] = sep == "1"
            if equal_width is not None:
                layout["column_equal_width"] = equal_width != "0"

        if sect_pr.find("w:titlePg", NS) is not None:
            layout["different_first_page_header_footer"] = True

        for tag_name, prefix in (("headerReference", "header"), ("footerReference", "footer")):
            refs = sect_pr.findall(f"w:{tag_name}", NS)
            if refs:
                layout[f"has_{prefix}"] = True
            for ref in refs:
                ref_type = ref.attrib.get(f"{{{W_NS}}}type")
                if ref_type:
                    layout[f"has_{ref_type}_{prefix}"] = True
        return layout

    def _half_points_to_pt_string(self, value: str) -> str:
        points = int(value) / 2
        if points.is_integer():
            return f"{int(points)}pt"
        return f"{points:.1f}pt"

    def _twips_to_inches_string(self, value: str) -> str:
        try:
            inches = int(value) / 1440
        except ValueError:
            return value
        return f"{inches:.2f}in"

    def _format_line_spacing(self, value: str, line_rule: str | None) -> str:
        if not value.isdigit():
            return value
        numeric = int(value)
        if line_rule == "auto":
            multiple = numeric / 240
            if multiple.is_integer():
                return f"{int(multiple)}.0 lines"
            return f"{multiple:.1f} lines"
        if line_rule in {"exact", "atLeast"}:
            points = numeric / 20
            if points.is_integer():
                return f"{int(points)}pt"
            return f"{points:.1f}pt"
        points = numeric / 20
        if points.is_integer():
            return f"{int(points)}pt"
        return f"{points:.1f}pt"

    def _is_enabled(self, el: ET.Element | None) -> bool:
        if el is None:
            return False
        value = el.attrib.get(f"{{{W_NS}}}val")
        return value not in {"0", "false", "False"}

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
