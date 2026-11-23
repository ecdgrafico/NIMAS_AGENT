#!/usr/bin/env python3
"""Build the editorial FM/EM proposals from their source fragments.

The output remains a merge-ready DTBook fragment: no dtbook/book wrappers.
Visual authority is the supplied FM and EM PDFs.  Trailing blank production
pages are deliberately not represented as editorial content.
"""
from copy import deepcopy
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
NS = "http://www.daisy.org/z3986/2005/dtbook/"
Q = lambda name: f"{{{NS}}}{name}"


def local(node):
    return etree.QName(node).localname


def text(node):
    return " ".join("".join(node.itertext()).split())


def element(name, value=None):
    node = etree.Element(Q(name), nsmap={None: NS})
    if value is not None:
        node.text = value
    return node


def fragment(path):
    raw = path.read_text(encoding="utf-8")
    return list(etree.fromstring(f"<root>{raw}</root>".encode("utf-8")))


def write(nodes, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\n\n".join(
        etree.tostring(node, encoding="UTF-8", pretty_print=True) for node in nodes
    ) + b"\n")


def first_heading(node):
    return next((child for child in node if local(child) in {"h1", "h2", "h3"}), None)


def shift_em_pages(node):
    """The EM source anchors are nine folios behind the visual PDF."""
    for page in node.iter(Q("pagenum")):
        value = text(page)
        if value.isdigit():
            corrected = int(value) + 9
            page.text = str(corrected)
            if page.get("id") == f"page-{value}":
                page.set("id", f"page-{corrected}")


def remediate_fm():
    nodes = fragment(ROOT / "lecciones_originales/FM.xml")
    doctitle = next(node for node in nodes if local(node) == "doctitle")
    author = next(node for node in nodes if local(node) == "docauthor")
    levels = [node for node in nodes if local(node) == "level1"]
    cover, credits, contents = levels[:3]

    # Pages i and ii are a single frontmatter unit: only the cover has a
    # visible heading; adding an invented "Credits" h1 would be misleading.
    cover_out = deepcopy(cover)
    title = next(child for child in cover_out if local(child) == "p")
    title.tag = Q("h1")
    logo = element("imggroup")
    image = element("img")
    image.set("id", "PHE27_SE_FM_pi_01_id")
    image.set("src", "images/FM/PHE27_SE_FM_pi_01.png")
    image.set("alt", "Vista Higher Learning logo")
    logo.append(image)
    subtitle = [child for child in cover_out if local(child) == "p"][0]
    cover_out.insert(list(cover_out).index(subtitle) + 1, logo)
    for child in credits:
        if local(child) != "pagenum":
            cover_out.append(deepcopy(child))
        else:
            cover_out.append(deepcopy(child))

    # The Contents spreads over iii-vii.  Keep one level1 and discard only
    # its presentational div wrapper; pagenum iv-vii stay at their exact spot.
    toc_out = deepcopy(contents)
    for wrapper in list(toc_out):
        if local(wrapper) == "div":
            position = list(toc_out).index(wrapper)
            toc_out.remove(wrapper)
            for offset, child in enumerate(list(wrapper)):
                toc_out.insert(position + offset, child)

    write([deepcopy(doctitle), deepcopy(author), cover_out, toc_out], ROOT / "secciones_propuestas/FM.xml")


def make_topic(old):
    topic = element("level3")
    heading = first_heading(old)
    topic.append(element("h3", text(heading) if heading is not None else "Index entry"))
    for child in old:
        if child is not heading:
            topic.append(deepcopy(child))
    return topic


def remediate_em():
    nodes = fragment(ROOT / "lecciones_originales/EM.xml")
    levels = [node for node in nodes if local(node) == "level1"]
    index_at = next(index for index, node in enumerate(levels)
                    if (heading := first_heading(node)) is not None and text(heading) == "INDEX")
    credits, photography = levels[:2]
    lessons = levels[2:index_at]
    index_levels = levels[index_at:]

    credits_out = element("level1")
    for child in credits:
        copied = deepcopy(child)
        if local(copied) == "p" and text(copied) == "CREDITS":
            copied.tag = Q("h1")
        credits_out.append(copied)
    photography_out = element("level2")
    photography_out.append(element("h2", text(first_heading(photography))))
    for child in photography:
        if child is not first_heading(photography):
            photography_out.append(deepcopy(child))
    for lesson in lessons:
        heading = first_heading(lesson)
        item = element("level3")
        item.append(element("h3", text(heading)))
        for child in lesson:
            if child is not heading:
                item.append(deepcopy(child))
        photography_out.append(item)
    credits_out.append(photography_out)
    shift_em_pages(credits_out)

    index_out = element("level1")
    index_out.append(element("h1", "INDEX"))
    current_letter = None
    current_topic = None
    for old_level in index_levels:
        heading = first_heading(old_level)
        # This is the legacy raster-page container.  It has no visible
        # heading or editorial text and corresponds to trailing blank pages.
        if heading is None:
            continue
        if heading is not None and text(heading) == "INDEX":
            children = [child for child in old_level if child is not heading]
        elif heading is not None and len(text(heading)) == 1 and text(heading).isalpha():
            current_letter = element("level2")
            current_letter.append(element("h2", text(heading)))
            index_out.append(current_letter)
            current_topic = None
            children = [child for child in old_level if child is not heading]
        else:
            # The original uses a top-level level1 for letters M, V and W.
            # Treat any one-letter h1 as the next alphabetical group.
            children = list(old_level)
        for child in children:
            if local(child) == "p" and len(text(child)) == 1 and text(child).isalpha():
                current_letter = element("level2")
                current_letter.append(element("h2", text(child)))
                index_out.append(current_letter)
                current_topic = None
            elif local(child) == "level2":
                if current_letter is None:
                    current_letter = element("level2")
                    current_letter.append(element("h2", "Index entries"))
                    index_out.append(current_letter)
                current_topic = make_topic(child)
                current_letter.append(current_topic)
            elif local(child) == "p":
                if current_topic is not None:
                    current_topic.append(deepcopy(child))
                elif current_letter is not None:
                    current_letter.append(deepcopy(child))
            elif local(child) == "pagenum":
                (current_letter if current_letter is not None else index_out).append(deepcopy(child))

    shift_em_pages(index_out)

    write([credits_out, index_out], ROOT / "secciones_propuestas/EM.xml")


if __name__ == "__main__":
    remediate_fm()
    remediate_em()
