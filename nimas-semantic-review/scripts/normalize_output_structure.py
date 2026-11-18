#!/usr/bin/env python3
"""Normalize the generated DTBook hierarchy without changing visible content."""
from pathlib import Path
import re
from lxml import etree

PACKAGE = Path("9781669952961NIMAS_corregido")
XML = PACKAGE / "9781669952961NIMAS.xml"
NS = "{http://www.daisy.org/z3986/2005/dtbook/}"


def local(node):
    return etree.QName(node).localname


def text(node):
    return " ".join("".join(node.itertext()).split())


def direct(node, name):
    return [x for x in node if local(x) == name]


tree = etree.parse(str(XML))
root = tree.getroot()
body = root.find(".//" + NS + "bodymatter")
lessons = direct(body, "level1")

# A next-lesson title that was placed before its printed page number belongs to
# the next level1, not to the preceding lesson.
for index, lesson in enumerate(lessons[:-1]):
    expected = str(index + 2)
    children = list(lesson)
    start = None
    for pos, child in enumerate(children):
        if local(child) != "level2":
            continue
        h2 = next(iter(direct(child, "h2")), None)
        if h2 is not None and text(h2) == f"Lesson {expected}":
            start = pos
            break
    if start is not None:
        destination = lessons[index + 1]
        insertion = 1 if direct(destination, "h1") else 0
        for child in children[start:]:
            lesson.remove(child)
            destination.insert(insertion, child)
            insertion += 1

for lesson in lessons:
    # A level heading leads its level; pagenum remains content, not structure.
    h1 = next(iter(direct(lesson, "h1")), None)
    if h1 is not None:
        lesson.remove(h1)
        lesson.insert(0, h1)

    # When a carried-forward printed lesson title has just been moved into its
    # proper level1, the generated h1 already represents that same title.
    # Retain it once, rather than exposing a duplicate h2 with identical text.
    h1_value = text(h1) if h1 is not None else ""
    for section in list(direct(lesson, "level2")):
        h2 = next(iter(direct(section, "h2")), None)
        if h2 is not None and text(h2) == h1_value:
            section.remove(h2)
            for child in list(section):
                section.remove(child)
                lesson.insert(lesson.index(section), child)
            lesson.remove(section)

    # Direct sections named solely by an activity letter are activities under
    # the preceding topical section. Their visible labels become A., B., etc.
    host = None
    for child in list(lesson):
        if local(child) != "level2":
            continue
        h2 = next(iter(direct(child, "h2")), None)
        heading = text(h2) if h2 is not None else ""
        match = re.match(r"^([A-M])(?:\.|\s|$)(.*)$", heading)
        if not match:
            host = child
            continue
        if host is None:
            continue
        letter, remainder = match.groups()
        child.tag = NS + "level3"
        h2.tag = NS + "h3"
        h2.clear()
        h2.text = f"{letter}." + (f" {remainder.strip()}" if remainder.strip() else "")
        lesson.remove(child)
        host.append(child)

    # Paragraph word/letter banks are semantic sidebars. Do not manufacture
    # text: the original paragraph content becomes list items only when it is
    # explicitly prefixed in the source.
    for p in list(lesson.xpath('.//d:p', namespaces={'d': root.nsmap[None]})):
        value = text(p)
        m = re.match(r"^(Letters|Words) to Use:\?\s*(.*)$", value, re.I)
        if not m:
            continue
        parent = p.getparent()
        sidebar = etree.Element(NS + "sidebar", render="required")
        hd = etree.SubElement(sidebar, NS + "hd")
        hd.text = f"{m.group(1).title()} to Use"
        values = m.group(2).split()
        if values:
            listing = etree.SubElement(sidebar, NS + "list", type="pl")
            for value in values:
                item = etree.SubElement(listing, NS + "li")
                item.text = value
        parent.replace(p, sidebar)

etree.indent(tree, space="", level=0)
tree.write(str(XML), encoding="UTF-8", xml_declaration=True, doctype=tree.docinfo.doctype)
