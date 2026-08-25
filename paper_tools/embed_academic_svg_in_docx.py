"""Replace seven raster figures in a DOCX with academic SVG figures.

The OOXML package keeps a high-resolution PNG as a compatibility fallback and
adds the native Office SVG extension.  The source document is never modified.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree


NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
NS_ASVG = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
SVG_EXTENSION_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
IMAGE_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
)


FIGURE_STEMS = [
    "fig01_two_sided_angle_locus_academic",
    "fig02_complete_candidates_academic",
    "fig03_identity_observation_separation_academic",
    "fig04_q1_schedule_matrix_academic",
    "fig05_q1_adjustment_errors_academic",
    "fig06_q2_lattice_academic",
    "fig07_q2_acceptance_ratios_academic",
]


def _next_relationship_number(relationships: etree._Element) -> int:
    numbers: list[int] = []
    for relationship in relationships:
        relationship_id = relationship.get("Id", "")
        if relationship_id.startswith("rId") and relationship_id[3:].isdigit():
            numbers.append(int(relationship_id[3:]))
    return max(numbers, default=0) + 1


def _copy_info(info: ZipInfo) -> ZipInfo:
    copied = ZipInfo(info.filename, date_time=info.date_time)
    copied.compress_type = ZIP_DEFLATED
    copied.comment = info.comment
    copied.extra = info.extra
    copied.create_system = info.create_system
    copied.external_attr = info.external_attr
    copied.internal_attr = info.internal_attr
    return copied


def embed_figures(
    input_docx: Path,
    output_docx: Path,
    svg_directory: Path,
    png_directory: Path,
) -> None:
    svg_paths = [svg_directory / f"{stem}.svg" for stem in FIGURE_STEMS]
    png_paths = [png_directory / f"{stem}.png" for stem in FIGURE_STEMS]
    missing = [p for p in [*svg_paths, *png_paths] if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing figure assets: {missing}")

    with ZipFile(input_docx, "r") as source_zip:
        document_root = etree.fromstring(source_zip.read("word/document.xml"))
        relationships_root = etree.fromstring(
            source_zip.read("word/_rels/document.xml.rels")
        )
        content_types_root = etree.fromstring(source_zip.read("[Content_Types].xml"))

        namespace_map = {"a": NS_A, "r": NS_R, "wp": NS_WP}
        blips = document_root.xpath(".//a:blip", namespaces=namespace_map)
        if len(blips) != len(FIGURE_STEMS):
            raise ValueError(
                f"Expected {len(FIGURE_STEMS)} inline figures, found {len(blips)}"
            )

        relationships_by_id = {
            element.get("Id"): element for element in relationships_root
        }
        next_rid_number = _next_relationship_number(relationships_root)
        fallback_targets: list[str] = []
        svg_package_names: list[str] = []

        for index, blip in enumerate(blips, start=1):
            fallback_rid = blip.get(f"{{{NS_R}}}embed")
            fallback_relationship = relationships_by_id.get(fallback_rid)
            if fallback_relationship is None:
                raise ValueError(f"Missing fallback relationship: {fallback_rid}")
            fallback_target = fallback_relationship.get("Target", "")
            fallback_package_name = str(
                PurePosixPath("word") / PurePosixPath(fallback_target)
            )
            fallback_targets.append(fallback_package_name)

            svg_filename = f"academic_figure_{index:02d}.svg"
            svg_package_name = f"word/media/{svg_filename}"
            svg_package_names.append(svg_package_name)
            svg_rid = f"rId{next_rid_number}"
            next_rid_number += 1

            relationship = etree.SubElement(
                relationships_root, f"{{{NS_REL}}}Relationship"
            )
            relationship.set("Id", svg_rid)
            relationship.set("Type", IMAGE_REL_TYPE)
            relationship.set("Target", f"media/{svg_filename}")

            for old_ext_list in blip.findall(f"{{{NS_A}}}extLst"):
                blip.remove(old_ext_list)
            ext_list = etree.SubElement(blip, f"{{{NS_A}}}extLst")
            extension = etree.SubElement(ext_list, f"{{{NS_A}}}ext")
            extension.set("uri", SVG_EXTENSION_URI)
            svg_blip = etree.SubElement(extension, f"{{{NS_ASVG}}}svgBlip")
            svg_blip.set(f"{{{NS_R}}}embed", svg_rid)

            inline = blip.getparent()
            while inline is not None and inline.tag != f"{{{NS_WP}}}inline":
                inline = inline.getparent()
            if inline is not None:
                doc_properties = inline.find(f"{{{NS_WP}}}docPr")
                if doc_properties is not None:
                    doc_properties.set("name", f"Academic vector figure {index}")
                    doc_properties.set(
                        "descr",
                        f"学术矢量图 {index}；源文件 {FIGURE_STEMS[index - 1]}.svg",
                    )

        has_svg_default = any(
            element.get("Extension", "").lower() == "svg"
            for element in content_types_root.findall(f"{{{NS_CT}}}Default")
        )
        if not has_svg_default:
            default = etree.SubElement(content_types_root, f"{{{NS_CT}}}Default")
            default.set("Extension", "svg")
            default.set("ContentType", "image/svg+xml")

        replacements: dict[str, bytes] = {
            "word/document.xml": etree.tostring(
                document_root,
                xml_declaration=True,
                encoding="UTF-8",
                standalone="yes",
            ),
            "word/_rels/document.xml.rels": etree.tostring(
                relationships_root,
                xml_declaration=True,
                encoding="UTF-8",
                standalone="yes",
            ),
            "[Content_Types].xml": etree.tostring(
                content_types_root,
                xml_declaration=True,
                encoding="UTF-8",
                standalone="yes",
            ),
        }
        replacements.update(
            {target: png.read_bytes() for target, png in zip(fallback_targets, png_paths)}
        )
        additions = {
            name: svg.read_bytes() for name, svg in zip(svg_package_names, svg_paths)
        }

        output_docx.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix="academic-vector-", suffix=".docx", dir=output_docx.parent
        )
        os.close(file_descriptor)
        temporary_path = Path(temporary_name)
        try:
            with ZipFile(temporary_path, "w", compression=ZIP_DEFLATED) as target_zip:
                for info in source_zip.infolist():
                    if info.filename in additions:
                        continue
                    data = replacements.get(info.filename, source_zip.read(info.filename))
                    target_zip.writestr(_copy_info(info), data)
                for package_name, data in additions.items():
                    target_zip.writestr(package_name, data)
            os.replace(temporary_path, output_docx)
        finally:
            temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_docx", type=Path)
    parser.add_argument("output_docx", type=Path)
    parser.add_argument("--svg-dir", type=Path, required=True)
    parser.add_argument("--png-dir", type=Path, required=True)
    arguments = parser.parse_args()

    embed_figures(
        arguments.input_docx.resolve(),
        arguments.output_docx.resolve(),
        arguments.svg_dir.resolve(),
        arguments.png_dir.resolve(),
    )
    print(f"OUTPUT_DOCX={arguments.output_docx.resolve()}")


if __name__ == "__main__":
    main()
