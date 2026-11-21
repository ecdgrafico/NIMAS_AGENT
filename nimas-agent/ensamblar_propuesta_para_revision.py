#!/usr/bin/env python3
"""Create a non-destructive DTBook candidate with one proposed lesson installed.

The source package is never changed.  The result is intended only for
structural review before an editor approves installation in the final package.
"""
import argparse
from copy import deepcopy
from pathlib import Path
from lxml import etree

NS = "http://www.daisy.org/z3986/2005/dtbook/"
Q = lambda name: f"{{{NS}}}{name}"


def page_numbers(element):
    values = []
    for page in element.xpath(".//d:pagenum[@page='normal']", namespaces={"d": NS}):
        text = "".join(page.itertext()).strip()
        if text.isdigit():
            values.append(int(text))
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson", type=int)
    parser.add_argument("start_page", type=int)
    parser.add_argument("end_page", type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    source = root / "9781669952961NIMAS_original" / "9781669952961NIMAS.xml"
    proposal = root / "lecciones_propuestas" / f"L{args.lesson:02d}.xml"
    destination = root / "nimas-review" / "ensamblados" / f"9781669952961NIMAS_L{args.lesson:02d}_propuesta.xml"
    if not proposal.is_file():
        raise SystemExit(f"No existe la propuesta: {proposal}")

    tree = etree.parse(str(source))
    candidate = etree.parse(str(proposal)).getroot()
    if etree.QName(candidate).localname != "level1":
        raise SystemExit("La propuesta debe tener level1 como raíz")
    body = tree.find(f".//{Q('bodymatter')}")
    removals = [node for node in body if page_numbers(node) and
                min(page_numbers(node)) >= args.start_page and
                max(page_numbers(node)) <= args.end_page]
    if not removals:
        raise SystemExit("No se encontraron nodos de origen para sustituir")
    insertion_index = body.index(removals[0])
    for node in removals:
        body.remove(node)
    body.insert(insertion_index, deepcopy(candidate))
    destination.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(destination), encoding="UTF-8", xml_declaration=True,
               doctype=tree.docinfo.doctype, pretty_print=True)
    print(destination)
    print(f"Sustituidos {len(removals)} nodos de origen por L{args.lesson:02d} (págs. {args.start_page}-{args.end_page}).")


if __name__ == "__main__":
    main()
