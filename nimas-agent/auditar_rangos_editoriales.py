#!/usr/bin/env python3
"""Detect source fragments whose editorial page range conflicts with its PDF.

This is a gate for reconstruction, not a validator of well-formed XML.  A
fragment can be valid XML yet be semantically wrong because pages leaked into
another lesson.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "PDF"
SOURCE = ROOT / "lecciones_originales"


def pages(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    return [int(value) for value in re.findall(
        r'<pagenum\b[^>]*\bpage=["\']normal["\'][^>]*>\s*(\d+)\s*</pagenum>', raw, re.I)]


def pdf_ranges():
    found = {}
    for pdf in PDF.glob("PHE27_SE_*.pdf"):
        match = re.search(r"PHE27_SE_(L\d\d|EM)_(\d+)-(\d+)_", pdf.name)
        if match:
            found[match.group(1)] = (int(match.group(2)), int(match.group(3)), pdf.name)
    return found


def issue_for(key, start, end, pdf):
    source = SOURCE / f"{key}.xml"
    if not source.is_file():
        return {"key": key, "required": True, "reason": "No existe el fragmento fuente.", "pdf": pdf}
    actual = pages(source)
    expected = set(range(start, end + 1))
    actual_set = set(actual)
    missing = sorted(expected - actual_set)
    outside = sorted(actual_set - expected)
    raw = source.read_text(encoding="utf-8", errors="replace")
    labels = []
    if key.startswith("L"):
        number = int(key[1:])
        foreign = sorted({int(value) for value in re.findall(r"<h1[^>]*>\s*Lesson\s+(\d+)", raw, re.I) if int(value) != number})
        if foreign:
            labels.append("Contiene encabezado de otra lección: " + ", ".join(f"Lesson {n}" for n in foreign))
    messages = []
    if missing: messages.append("Faltan páginas del PDF: " + ", ".join(map(str, missing)))
    if outside: messages.append("Incluye páginas fuera de rango: " + ", ".join(map(str, outside)))
    messages += labels
    return {"key": key, "required": bool(messages), "reason": "; ".join(messages), "pdf": pdf,
            "expected": [start, end], "actual": actual}


def main():
    audits = [issue_for(key, start, end, pdf) for key, (start, end, pdf) in pdf_ranges().items()]
    print(json.dumps({item["key"]: item for item in audits}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
