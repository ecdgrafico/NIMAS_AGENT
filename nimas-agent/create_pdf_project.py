#!/usr/bin/env python3
"""Create a non-destructive NIMAS workspace starting from one or more PDFs.

This is the intake stage only: it inventories pages and text and leaves
semantic XML generation for a later, auditable provider step.
"""
import argparse
import hashlib
import json
import shutil
import re
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

def classify(filename: str) -> str:
    stem = Path(filename).stem.upper()
    if re.search(r"(^|[_\- ])FM([_\- .]|$)|FRONTMATTER|FRONT_MATTER", stem): return "frontmatter"
    if re.search(r"(^|[_\- ])EM([_\- .]|$)|REARMATTER|REAR_MATTER", stem): return "rearmatter"
    if re.search(r"(^|[_\- ])(?:L|U|PL|IU|UI)\d*([_\- .]|$)|LESSON|UNIT|CHAPTER|PRELIMINARY|INTRODUCTORY", stem): return "bodymatter"
    return "unclassified"

def unit_sort(item):
    section_order = {"frontmatter": 0, "bodymatter": 1, "rearmatter": 2, "unclassified": 3}
    match = re.search(r"(?:L|U|PL|IU|UI)(\d+)", item["file"].upper())
    return (section_order.get(item["section"], 9), int(match.group(1)) if match else 999, item["file"].lower())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True, help="PDF file or folder")
    parser.add_argument("--destino", type=Path, required=True, help="New project folder")
    parser.add_argument("--nombre", default="Proyecto NIMAS", help="Project display name")
    args = parser.parse_args()

    source = args.pdf.resolve()
    pdfs = [source] if source.is_file() else sorted(source.rglob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No encontré PDFs en: {source}")
    if args.destino.exists() and any(args.destino.iterdir()):
        raise SystemExit(f"El destino debe estar vacío: {args.destino}")

    root = args.destino.resolve()
    (root / "fuentes" / "pdf").mkdir(parents=True, exist_ok=True)
    for folder in ("metadata", "structure", "inventario", "imagenes_detectadas", "working", "propuestas", "revision", "versions", "deliverables"):
        (root / folder).mkdir(exist_ok=True)

    documents = []
    for pdf in pdfs:
        target = root / "fuentes" / "pdf" / pdf.name
        shutil.copy2(pdf, target)
        reader = PdfReader(str(pdf))
        pages = []
        for number, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            pages.append({"page": number, "text": text, "text_length": len(text)})
        documents.append({"file": pdf.name, "sha256": sha256(target), "pages": pages})

    inventory = {
        "schema": "nimas-project/1",
        "name": args.nombre,
        "source_mode": "pdf_only",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "documents": documents,
        "xml_source": None,
        "reference_lessons": [],
        "status": "intake_complete",
        "next": "generate_auditable_dtbook_proposal",
    }
    (root / "inventario" / "project.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "metadata" / "nimac.json").write_text(json.dumps({"title": args.nombre}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    units = [{"id": Path(item["file"]).stem, "name": Path(item["file"]).stem, "section": classify(item["file"]), "file": item["file"], "pages": [1, len(item["pages"])]} for item in documents]
    units.sort(key=unit_sort)
    (root / "structure" / "structure.json").write_text(json.dumps({"units": units}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "project.yaml").write_text(
        f"name: {args.nombre!r}\nsource_mode: pdf_only\npdf_dir: fuentes/pdf\nxml_source: null\nstatus: intake_complete\n",
        encoding="utf-8",
    )
    print(f"Proyecto PDF creado: {root}")
    print(f"PDFs inventariados: {len(documents)}")
    print(f"Páginas inventariadas: {sum(len(item['pages']) for item in documents)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
