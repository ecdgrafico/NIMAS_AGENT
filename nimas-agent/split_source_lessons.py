#!/usr/bin/env python3
"""Split source XML into merge-ready DTBook fragments.

The source package is never changed. Lesson files contain only their level1;
FM/EM contain only their internal section children. The reviewed source is
parsed in recovery mode so its later malformed markup cannot prevent
preservation of the three manually reviewed lessons.
"""
from copy import deepcopy
from pathlib import Path
import re

from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
NS = "http://www.daisy.org/z3986/2005/dtbook/"
Q = lambda name: f"{{{NS}}}{name}"
LESSON = re.compile(r"^Lesson\s+(\d+)\s*$", re.I)
RANGES = {lesson: (1 + (lesson - 1) * 12, 12 + (lesson - 1) * 12)
          for lesson in range(1, 23)}
RANGES.update({23: (265, 274), 24: (275, 286)})


def text(node):
    return " ".join("".join(node.itertext()).split())


def normal_pages(node):
    pages = []
    for page in node.iter(Q("pagenum")):
        if page.get("page") != "normal":
            continue
        try:
            pages.append(int(text(page)))
        except ValueError:
            pass
    return pages


def write_fragment(nodes, path):
    """Write elements without XML/DTBook envelope or declaration."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b"\n".join(
        etree.tostring(deepcopy(node), encoding="UTF-8", pretty_print=True)
        for node in nodes
    )
    path.write_bytes(payload + b"\n")


def split_original():
    source = ROOT / "9781669952961NIMAS_original/9781669952961NIMAS.xml"
    tree = etree.parse(str(source))
    out = ROOT / "lecciones_originales"
    book = tree.getroot().find(Q("book"))

    # FM is a fragment to be placed inside frontmatter at merge time.
    source_fm = book.find(Q("frontmatter"))
    write_fragment(list(source_fm), out / "FM.xml")

    body = book.find(Q("bodymatter"))
    for lesson, (start, end) in RANGES.items():
        nodes = [child for child in body if (pages := normal_pages(child))
                 and start <= min(pages) <= end]
        write_fragment(nodes, out / f"L{lesson:02d}.xml")

    # The PDF source calls the complete rear matter EM, even though the
    # original XML labels it rearmatter.  Keep it intact: its legacy printed
    # page anchors are not reliable enough to trim it by number.
    source_rm = book.find(Q("rearmatter"))
    write_fragment(list(source_rm), out / "EM.xml")


def split_reviewed_samples():
    source = ROOT / "9781669952961NIMAS/9781669952961NIMAS.xml"
    parser = etree.XMLParser(recover=True, remove_blank_text=True)
    tree = etree.parse(str(source), parser)
    out = ROOT / "lecciones_remediadas"
    body = tree.find(f".//{Q('bodymatter')}")
    found = set()
    for child in body:
        if etree.QName(child).localname != "level1":
            continue
        h1 = next((node for node in child if etree.QName(node).localname == "h1"), None)
        match = LESSON.match(text(h1)) if h1 is not None else None
        if not match:
            continue
        lesson = int(match.group(1))
        if lesson not in {1, 2, 3}:
            continue
        write_fragment([child], out / f"L{lesson:02d}.xml")
        found.add(lesson)
    missing = {1, 2, 3} - found
    if missing:
        raise SystemExit(f"Could not isolate reviewed lessons: {sorted(missing)}")


if __name__ == "__main__":
    split_original()
    split_reviewed_samples()
