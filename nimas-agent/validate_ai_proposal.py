#!/usr/bin/env python3
"""Validate a proposed DTBook fragment before human approval."""
import argparse, json
from pathlib import Path
from lxml import etree

FORBIDDEN = {"dtbook", "book", "bodymatter", "frontmatter", "rearmatter", "package"}

def validate(path: Path):
    errors = []
    try:
        root = etree.parse(str(path)).getroot()
    except (OSError, etree.XMLSyntaxError) as exc:
        return {"status": "fail", "path": str(path), "errors": [f"XML no bien formado: {exc}"]}
    if root.tag != "level1": errors.append(f"La raíz debe ser level1 y es {root.tag}")
    levels = {f"level{i}": i for i in range(1, 7)}
    for element in root.iter():
        if element.tag in FORBIDDEN and element is not root:
            errors.append(f"Contenedor de paquete no permitido: {element.tag}")
        parent = element.getparent()
        if element.tag in levels and parent is not None and parent.tag in levels and levels[element.tag] > levels[parent.tag] + 1:
            errors.append(f"Nivel inválido: {parent.tag} contiene {element.tag}")
    return {"status": "pass" if not errors else "fail", "path": str(path), "errors": errors}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("xml", type=Path); ap.add_argument("--report", type=Path)
    args = ap.parse_args(); result = validate(args.xml)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False)); raise SystemExit(0 if result["status"] == "pass" else 1)

if __name__ == "__main__": main()
