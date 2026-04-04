# тянем plain text из docx через zip+xml, без сторонних либ
from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def extract_plain_text_from_docx(path: str) -> str:
    # w:t + w:tab из document.xml; кривой zip/xml → ""
    parts: list[str] = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            try:
                raw = zf.read("word/document.xml")
            except KeyError:
                return ""
    except (zipfile.BadZipFile, OSError):
        return ""

    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return ""

    t_tag = f"{{{W_NS}}}t"
    tab_tag = f"{{{W_NS}}}tab"
    for el in root.iter():
        if el.tag == t_tag:
            if el.text:
                parts.append(el.text)
            if el.tail:
                parts.append(el.tail)
        elif el.tag == tab_tag:
            parts.append("\t")

    return " ".join(s for s in parts if s).strip()
