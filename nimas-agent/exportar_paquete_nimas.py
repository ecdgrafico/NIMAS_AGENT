#!/usr/bin/env python3
"""Assemble approved NIMAS fragments into a new, validated ZIP package."""
from copy import deepcopy
from datetime import datetime
import json
import mimetypes
from pathlib import Path
import re
import shutil
import sys
import zipfile

from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
NS = "http://www.daisy.org/z3986/2005/dtbook/"
Q = lambda name: f"{{{NS}}}{name}"
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml"}
# Algunos recursos heredados conservan el folio de extracción en el nombre,
# aunque su relación editorial correcta está en la página vecina.
RESOURCE_PAGE_EXCEPTIONS = {
    "images/L19/PHE27_SE_L19_p226_03.png": "Se asocia al ítem 4 de la p. 225 (manos al piano); el nombre heredado p226 no describe su página editorial.",
}


def local(node): return etree.QName(node).localname
def text(node): return "".join(node.itertext()).strip()


def write_left_aligned(tree, target):
    """Write readable XML without leading tabs/spaces on markup lines."""
    payload = etree.tostring(tree, encoding="UTF-8", xml_declaration=True,
                             doctype=tree.docinfo.doctype, pretty_print=True).decode("UTF-8")
    target.write_text(re.sub(r"(?m)^[\\t ]+", "", payload), encoding="UTF-8")


def approved_units():
    record = (ROOT / "nimas-review" / "registro-aprobaciones.md").read_text(encoding="utf-8")
    lessons = {int(value) for value in re.findall(r"\| L(\d{2}) \|[^|]*\| Aprobada", record)}
    editorials = set(re.findall(r"\| (FM|EM) \|[^|]*\| Aprobada", record))
    missing = [f"L{number:02d}" for number in range(4, 25) if number not in lessons]
    missing += sorted({"FM", "EM"} - editorials)
    if missing:
        raise ValueError("No se puede exportar: faltan aprobaciones para " + ", ".join(missing))


def fragment(path):
    raw = path.read_text(encoding="utf-8")
    return list(etree.fromstring(f"<root xmlns=\"{NS}\">{raw}</root>".encode("utf-8")))


def replace_children(parent, nodes):
    for child in list(parent): parent.remove(child)
    for node in nodes: parent.append(deepcopy(node))


def image_id(relative, used):
    base = "image_" + re.sub(r"[^A-Za-z0-9_]+", "_", str(relative.with_suffix("")))
    value = base
    index = 2
    while value in used:
        value = f"{base}_{index}"; index += 1
    used.add(value)
    return value


def rebuild_opf(package, original_opf):
    # El OPF fuente conserva espacios de formato irregulares. Al descartarlos
    # antes de serializar, lxml puede emitir un elemento por línea; después se
    # elimina la sangría, pero no los saltos de línea.
    tree = etree.parse(str(original_opf), parser=etree.XMLParser(remove_blank_text=True))
    root = tree.getroot(); namespace = root.nsmap.get(None)
    manifest = root.find(f"{{{namespace}}}manifest")
    for item in list(manifest):
        if item.get("media-type", "").startswith("image/"):
            manifest.remove(item)
    used = {item.get("id") for item in manifest if item.get("id")}
    for image in sorted((package / "images").rglob("*")):
        if not image.is_file() or image.suffix.lower() not in IMAGE_TYPES:
            continue
        relative = image.relative_to(package)
        etree.SubElement(manifest, f"{{{namespace}}}item", id=image_id(relative, used),
                         href=str(relative), **{"media-type": IMAGE_TYPES[image.suffix.lower()]})
    target = package / original_opf.name
    write_left_aligned(tree, target)


def prune_unreferenced_images(package, xml_path):
    """Keep the final package free of image files not used by DTBook.

    Source folders may retain decorative or abandoned extraction crops.  They
    must not leak into the deliverable or its OPF manifest merely because they
    are physical files in the working package.
    """
    tree = etree.parse(str(xml_path))
    references = {node.get("src") for node in tree.iter(Q("img")) if node.get("src")}
    removed = []
    for image in (package / "images").rglob("*"):
        if not image.is_file() or image.suffix.lower() not in IMAGE_TYPES:
            continue
        relative = str(image.relative_to(package))
        if relative not in references:
            removed.append(relative)
            image.unlink()
    return removed


def validate(package):
    xml_path = next(package.glob("*.xml"))
    opf_path = next(package.glob("*.opf"))
    tree = etree.parse(str(xml_path)); root = tree.getroot()
    pages = [int(text(node)) for node in tree.iter(Q("pagenum")) if node.get("page") == "normal"]
    expected = list(range(1, 298))
    if pages != expected:
        raise ValueError("La paginación normal final no es la secuencia 1–297.")
    references = {node.get("src") for node in tree.iter(Q("img")) if node.get("src")}
    if missing := sorted(src for src in references if not (package / src).is_file()):
        raise ValueError("XML referencia imágenes inexistentes: " + ", ".join(missing[:5]))
    opf = etree.parse(str(opf_path)); namespace = opf.getroot().nsmap.get(None)
    manifest = {node.get("href") for node in opf.findall(f".//{{{namespace}}}manifest/{{{namespace}}}item") if node.get("href")}
    if missing := sorted(references - manifest):
        raise ValueError("OPF no declara imágenes usadas por el XML: " + ", ".join(missing[:5]))
    if absent := sorted(href for href in manifest if not (package / href).is_file()):
        raise ValueError("OPF contiene recursos inexistentes: " + ", ".join(absent[:5]))
    physical_images = {
        str(path.relative_to(package)) for path in (package / "images").rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_TYPES
    }
    if unused := sorted(physical_images - references):
        raise ValueError("El paquete conserva imágenes sin referencia XML: " + ", ".join(unused[:5]))
    dtd = etree.DTD(str(ROOT / "nimas-agent" / "dtbook-2005-3.dtd"))
    if not dtd.validate(tree):
        errors = "; ".join(str(error) for error in list(dtd.error_log)[:3])
        raise ValueError("El DTBook ensamblado no valida contra el DTD: " + errors)
    return {
        "xmlImages": len(references),
        "opfImageResources": sum(1 for href in manifest if Path(href).suffix.lower() in IMAGE_TYPES),
        "resourcePageExceptions": RESOURCE_PAGE_EXCEPTIONS,
    }


def main():
    approved_units()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    export_root = ROOT / "nimas-export" / stamp
    package = export_root / "9781669952961NIMAS"
    source_package = ROOT / "9781669952961NIMAS"
    original_package = ROOT / "9781669952961NIMAS_original"
    shutil.copytree(source_package, package, ignore=shutil.ignore_patterns(".DS_Store"))

    tree = etree.parse(str(original_package / "9781669952961NIMAS.xml"))
    book = tree.getroot().find(Q("book"))
    replace_children(book.find(Q("frontmatter")), fragment(ROOT / "secciones_propuestas/FM.xml"))
    body = book.find(Q("bodymatter")); replace_children(body, [])
    for number in range(1, 25):
        proposal = ROOT / ("lecciones_remediadas" if number <= 3 else "lecciones_propuestas") / f"L{number:02d}.xml"
        node = etree.parse(str(proposal)).getroot()
        body.append(deepcopy(node))
    replace_children(book.find(Q("rearmatter")), fragment(ROOT / "secciones_propuestas/EM.xml"))
    xml_target = package / "9781669952961NIMAS.xml"
    write_left_aligned(tree, xml_target)
    removed_images = prune_unreferenced_images(package, xml_target)
    rebuild_opf(package, original_package / "9781669952961NIMAS.opf")
    checks = validate(package)

    zip_path = export_root / "9781669952961NIMAS-remediado.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in package.rglob("*"):
            if path.is_file() and path.name != ".DS_Store":
                archive.write(path, path.relative_to(export_root))
    report = {"status": "pass", "package": str(package.relative_to(ROOT)), "zip": str(zip_path.relative_to(ROOT)), "normalPages": "1–297", "removedUnreferencedImages": removed_images, **checks}
    (export_root / "validacion.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    try: main()
    except Exception as error:
        print(json.dumps({"status": "blocked", "error": str(error)}))
        sys.exit(1)
