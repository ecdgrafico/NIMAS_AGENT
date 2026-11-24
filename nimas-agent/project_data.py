"""Read/write the neutral project model used by the PDF-first workspace."""
import json
import re
from pathlib import Path
from pypdf import PdfReader

DEFAULT_METADATA = {
    "title": "", "creators": [], "publisher": "", "identifier": "",
    "source_isbns": [], "language": "en", "subjects": [], "grade_levels": [],
    "copyright_year": "", "publication_year": "", "edition": "",
    "state_edition": "National ed.", "content_type": "Textbook", "series": "",
}

def ensure_pdf_project_layout(root: Path):
    """Backfill the neutral model for projects created by earlier app builds."""
    if not (root / "project.yaml").is_file(): return
    (root / "metadata").mkdir(exist_ok=True); (root / "structure").mkdir(exist_ok=True)
    metadata_path = root / "metadata" / "nimac.json"
    if not metadata_path.is_file(): metadata_path.write_text(json.dumps({"title": root.name}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    structure_path = root / "structure" / "structure.json"
    if structure_path.is_file(): return
    pdf_root = root / "fuentes" / "pdf"
    units = []
    for pdf in sorted(pdf_root.rglob("*.pdf")) if pdf_root.is_dir() else []:
        try: pages = len(PdfReader(str(pdf)).pages)
        except Exception: pages = 0
        stem = pdf.stem.upper()
        if re.search(r"(^|[_\- ])FM([_\- .]|$)|FRONTMATTER|FRONT_MATTER", stem): section = "frontmatter"
        elif re.search(r"(^|[_\- ])EM([_\- .]|$)|REARMATTER|REAR_MATTER", stem): section = "rearmatter"
        elif re.search(r"(^|[_\- ])(?:L|U|PL|IU|UI)\d*([_\- .]|$)|LESSON|UNIT|CHAPTER|PRELIMINARY|INTRODUCTORY", stem): section = "bodymatter"
        else: section = "unclassified"
        units.append({"id": pdf.stem, "name": pdf.stem, "section": section, "file": str(pdf.relative_to(pdf_root)), "pages": [1, pages]})
    structure_path.write_text(json.dumps({"units": units}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def load_project(root: Path):
    ensure_pdf_project_layout(root)
    inventory_path = root / "inventario" / "project.json"
    data = json.loads(inventory_path.read_text(encoding="utf-8")) if inventory_path.is_file() else {}
    metadata_path = root / "metadata" / "nimac.json"
    metadata = {**DEFAULT_METADATA, **(json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {})}
    structure_path = root / "structure" / "structure.json"
    structure = json.loads(structure_path.read_text(encoding="utf-8")) if structure_path.is_file() else {"units": []}
    return {"inventory": data, "metadata": metadata, "structure": structure}

def save_project(root: Path, metadata=None, structure=None):
    (root / "metadata").mkdir(exist_ok=True)
    (root / "structure").mkdir(exist_ok=True)
    if metadata is not None:
        (root / "metadata" / "nimac.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if structure is not None:
        (root / "structure" / "structure.json").write_text(json.dumps(structure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
