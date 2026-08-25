"""Replace only Chinese full stops immediately following Word OMML equations.

This is a presentation-only OOXML patch: formulas, numbering, and ordinary
Chinese prose punctuation are untouched.
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "paper_drafts" / "2022国赛B题论文_图表补全版.docx"
OUTPUT = ROOT / "paper_drafts" / "2022国赛B题论文_图表补全版_公式句号英文版.docx"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS = {"w": W_NS, "m": M_NS}


def is_math(child: etree._Element) -> bool:
    return child.tag in {f"{{{M_NS}}}oMath", f"{{{M_NS}}}oMathPara"}


def first_text_run(child: etree._Element):
    texts = child.xpath(".//w:t", namespaces=NS)
    return texts[0] if texts else None


def patch_xml(blob: bytes) -> tuple[bytes, int]:
    root = etree.fromstring(blob)
    changes = 0
    for paragraph in root.xpath(".//w:p", namespaces=NS):
        after_math = False
        for child in paragraph:
            if is_math(child):
                after_math = True
                continue
            if not after_math:
                continue
            if child.tag == f"{{{W_NS}}}r":
                node = first_text_run(child)
                if node is None or node.text is None:
                    continue
                lead = len(node.text) - len(node.text.lstrip())
                if len(node.text) > lead and node.text[lead] == "。":
                    node.text = node.text[:lead] + "." + node.text[lead + 1:]
                    changes += 1
                after_math = False
            elif child.tag not in {f"{{{W_NS}}}bookmarkStart", f"{{{W_NS}}}bookmarkEnd", f"{{{W_NS}}}proofErr"}:
                # A real non-formula element begins: the punctuation is no longer
                # immediately attached to the equation.
                after_math = False
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), changes


def main() -> None:
    if not TARGET.exists():
        raise FileNotFoundError(TARGET)
    total = 0
    with ZipFile(TARGET, "r") as source, ZipFile(OUTPUT, "w", ZIP_DEFLATED) as destination:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                data, count = patch_xml(data)
                total += count
            destination.writestr(item, data)
    print(f"FORMULA_TRAILING_CHINESE_FULL_STOPS_REPLACED={total}")
    print(f"OUTPUT={OUTPUT}")


if __name__ == "__main__":
    main()
