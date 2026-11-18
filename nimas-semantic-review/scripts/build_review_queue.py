#!/usr/bin/env python3
"""Create or refresh a page-by-page NIMAS correction queue.

The queue is a work-control artifact, not a semantic converter. It records the
PDF source, current DTBook location, extracted images, unresolved resource
issues, and an explicit human review state for every editorial page.
"""

import argparse
import json
from pathlib import Path
import re

from lxml import etree

NS = {"d": "http://www.daisy.org/z3986/2005/dtbook/"}


def lesson_ranges():
    for lesson in range(1, 23):
        yield lesson, (lesson - 1) * 12 + 1, lesson * 12
    yield 23, 265, 274
    yield 24, 275, 286


def load_prior(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {record["key"]: record for record in data.get("records", [])}


def xml_page_data(xml_tree, page):
    nodes = xml_tree.xpath(f'//d:pagenum[normalize-space()="{page}"]', namespaces=NS)
    if not nodes:
        return {"found": False, "line": None, "imageRefs": []}
    node = nodes[0]
    next_nodes = node.xpath("following::d:pagenum[1]", namespaces=NS)
    stop_line = next_nodes[0].sourceline if next_nodes else 10**9
    refs = []
    for image in node.xpath("following::d:img", namespaces=NS):
        if image.sourceline >= stop_line:
            break
        refs.append(image.get("src"))
    return {"found": True, "line": node.sourceline, "imageRefs": refs}


def assets_for_page(image_dir, page):
    pattern = re.compile(rf"_p{page:03d}_\d+\.png$")
    return sorted(str(path.relative_to(image_dir.parent.parent)).replace("\\", "/")
                  for path in image_dir.glob("*.png") if pattern.search(path.name))


def record(key, unit, page, pdf, page_data, assets, prior):
    previous = prior.get(key, {})
    refs = page_data["imageRefs"]
    issues = []
    if not page_data["found"]:
        issues.append("pagenum missing from XML")
    if any("/u" in reference or reference.startswith("images/fm/") or reference.startswith("images/em/")
           for reference in refs):
        issues.append("legacy image reference")
    if len(refs) != len(assets):
        issues.append(f"image-count mismatch: xml={len(refs)}, extracted={len(assets)}")
    return {
        "key": key,
        "unit": unit,
        "page": page,
        "pdf": pdf,
        "xml": {"pagenumLine": page_data["line"], "imageRefs": refs},
        "extractedImages": assets,
        "status": previous.get("status", "pending"),
        "checks": previous.get("checks", {
            "pdfVisualReview": False,
            "semanticXmlCorrected": False,
            "imagePlacementCorrected": False,
            "opfCrossChecked": False,
            "xmlValidatedAfterEdit": False,
        }),
        "issues": issues,
        "notes": previous.get("notes", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("pdf_dir", type=Path)
    parser.add_argument("queue", type=Path)
    parser.add_argument("--set-status", nargs=2, metavar=("KEY", "STATUS"))
    parser.add_argument("--set-prefix", nargs=2, metavar=("PREFIX", "STATUS"))
    args = parser.parse_args()

    prior = load_prior(args.queue)
    if args.set_status:
        key, status = args.set_status
        if key not in prior:
            raise SystemExit(f"Unknown queue key: {key}")
        if status not in {"pending", "in_progress", "complete", "blocked"}:
            raise SystemExit("Status must be pending, in_progress, complete, or blocked")
        prior[key]["status"] = status
    if args.set_prefix:
        prefix, status = args.set_prefix
        if status not in {"pending", "in_progress", "complete", "blocked"}:
            raise SystemExit("Status must be pending, in_progress, complete, or blocked")
        matches = [key for key in prior if key.startswith(prefix)]
        if not matches:
            raise SystemExit(f"No queue records match: {prefix}")
        for key in matches:
            prior[key]["status"] = status

    xml_path = args.package / "9781669952961NIMAS.xml"
    xml = etree.parse(str(xml_path))
    records = []

    # FM pages i–vii; the final PDF page viii is intentionally omitted as blank.
    fm_pdf = "PHE27_SE_FM_i-iv_hi.pdf"
    for roman in ("i", "ii", "iii", "iv", "v", "vi", "vii"):
        key = f"FM-{roman}"
        node = xml.xpath(f'//d:pagenum[normalize-space()="{roman}"]', namespaces=NS)
        line = node[0].sourceline if node else None
        refs = []
        if node:
            following = node[0].xpath("following::d:pagenum[1]", namespaces=NS)
            stop = following[0].sourceline if following else 10**9
            for image in node[0].xpath("following::d:img", namespaces=NS):
                if image.sourceline >= stop:
                    break
                refs.append(image.get("src"))
        prior_record = prior.get(key, {})
        records.append({"key": key, "unit": "FM", "page": roman, "pdf": fm_pdf,
                        "xml": {"pagenumLine": line, "imageRefs": refs},
                        "extractedImages": ["images/FM/PHE27_SE_FM_pi_01.png"] if roman == "i" else [],
                        "status": prior_record.get("status", "pending"),
                        "checks": prior_record.get("checks", {"pdfVisualReview": False, "semanticXmlCorrected": False, "imagePlacementCorrected": False, "opfCrossChecked": False, "xmlValidatedAfterEdit": False}),
                        "issues": [] if node else ["pagenum missing from XML"],
                        "notes": prior_record.get("notes", "")})

    for lesson, first, last in lesson_ranges():
        label = f"L{lesson:02d}"
        pdf = next(args.pdf_dir.glob(f"PHE27_SE_{label}_*_hi.pdf")).name
        image_dir = args.package / "images" / label
        for page in range(first, last + 1):
            key = f"{label}-{page:03d}"
            records.append(record(key, label, page, pdf, xml_page_data(xml, page),
                                  assets_for_page(image_dir, page), prior))

    # EM 287–297 have content; 298–304 are intentionally omitted as blank.
    em_pdf = "PHE27_SE_EM_287-304_hi.pdf"
    for page in range(287, 298):
        key = f"EM-{page}"
        records.append(record(key, "EM", page, em_pdf, xml_page_data(xml, page), [], prior))

    summary = {}
    for item in records:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    args.queue.parent.mkdir(parents=True, exist_ok=True)
    args.queue.write_text(json.dumps({"package": str(args.package), "summary": summary,
                                      "records": records}, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
