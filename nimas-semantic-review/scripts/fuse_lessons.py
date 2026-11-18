#!/usr/bin/env python3
"""Fuse page-split DTBook lesson containers into lesson-level hierarchy.

This is deliberately conservative: it keeps every child node and text value,
promotes page-level h1s to h2s, and moves continued unheaded pages into the
preceding section. It does not replace editorial text or create image mappings.
"""

from copy import deepcopy
from pathlib import Path
import re
import sys

from lxml import etree

NS = "http://www.daisy.org/z3986/2005/dtbook/"
LESSON = re.compile(r"^Lesson\s+(?:[1-9]|1[0-9]|2[0-4])\s*$")


def tag(name: str) -> str:
    return f"{{{NS}}}{name}"


def direct_heading(element, name: str):
    return next((child for child in element if child.tag == tag(name)), None)


def shift_nested_levels(section):
    # Work deepest-first so nested hierarchy retains its relative depth.
    for depth in range(6, 1, -1):
        for element in section.iter(tag(f"level{depth}")):
            element.tag = tag(f"level{depth + 1}")
            heading = direct_heading(element, f"h{depth}")
            if heading is not None:
                heading.tag = tag(f"h{depth + 1}")


def main(source: Path, output: Path):
    tree = etree.parse(str(source), etree.XMLParser(remove_blank_text=False))
    body = tree.find(f".//{tag('bodymatter')}")
    if body is None:
        raise ValueError("No se encontró bodymatter.")

    children = list(body)
    for child in children:
        body.remove(child)

    lesson_root = None
    last_section = None
    lesson_count = 0
    anomalies = []

    for child in children:
        if child.tag != tag("level1"):
            raise ValueError(f"Hijo inesperado de bodymatter: {child.tag}")

        h1s = [node for node in child if node.tag == tag("h1")]
        first_text = "".join(h1s[0].itertext()).strip() if h1s else ""

        if h1s and LESSON.fullmatch(first_text):
            if lesson_root is not None:
                body.append(lesson_root)
            lesson_root = child
            last_section = None
            lesson_count += 1
            continue

        if lesson_root is None:
            anomalies.append("Contenido anterior a Lesson 1 preservado como level1.")
            body.append(child)
            continue

        if h1s:
            child.tag = tag("level2")
            h1s[0].tag = tag("h2")
            for duplicate in h1s[1:]:
                duplicate.tag = tag("p")
                anomalies.append("Se conservó un h1 adicional como p; requiere revisión PDF.")
            shift_nested_levels(child)
            lesson_root.append(child)
            last_section = child
        elif last_section is not None:
            for grandchild in list(child):
                child.remove(grandchild)
                last_section.append(grandchild)
        else:
            child.tag = tag("level2")
            shift_nested_levels(child)
            lesson_root.append(child)
            last_section = child

    if lesson_root is not None:
        body.append(lesson_root)

    if lesson_count != 24:
        raise ValueError(f"Se esperaban 24 lecciones; se encontraron {lesson_count}.")

    etree.indent(tree, space="", level=0)
    output.write_bytes(etree.tostring(tree, encoding="UTF-8", xml_declaration=True, doctype=tree.docinfo.doctype))
    return lesson_count, anomalies


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: fuse_lessons.py entrada.xml salida.xml")
    count, anomalies = main(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"Lecciones fusionadas: {count}")
    for item in anomalies:
        print(f"AVISO: {item}")
