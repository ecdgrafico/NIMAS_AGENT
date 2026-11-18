#!/usr/bin/env python3
"""First PDF-led semantic repair pass for Lesson 2.

This intentionally changes only the working reconstruction.  The original
package is never an input-output target.
"""
from copy import deepcopy
from lxml import etree
from pathlib import Path
import re

NS = "http://www.daisy.org/z3986/2005/dtbook/"
Q = lambda name: f"{{{NS}}}{name}"
ACTIVITY = re.compile(r"^([A-E])(?:[.\s]+)(.+)$", re.S)

def text(el):
    return "".join(el.itertext()).strip()

def pagenum(el):
    found = el.xpath('.//d:pagenum[@page="normal"]', namespaces={"d": NS})
    return int(text(found[0])) if found and text(found[0]).isdigit() else None

def promote_children(level, old_depth, new_depth):
    """Adjust nested level/head names after a former level1 becomes level2."""
    for child in level.iterdescendants():
        local = etree.QName(child).localname
        if local.startswith("level") and local[5:].isdigit():
            n = int(local[5:])
            if n >= old_depth:
                child.tag = Q(f"level{min(n + (new_depth-old_depth), 6)}")
        elif local.startswith("h") and local[1:].isdigit():
            n = int(local[1:])
            if n >= old_depth:
                child.tag = Q(f"h{min(n + (new_depth-old_depth), 6)}")

def split_activities(container, depth):
    """Turn direct A–E instructions into sibling nested activity levels."""
    kids = list(container)
    starts = []
    for i, child in enumerate(kids):
        if etree.QName(child).localname != "p":
            continue
        m = ACTIVITY.match(text(child))
        # A letter-pair such as "C c" is course content, not an activity.
        if m and len(m.group(2).strip()) > 3:
            starts.append((i, m))
    for i, match in reversed(starts):
        child = kids[i]
        # The list may have changed because later activities were already moved.
        if child.getparent() is not container:
            continue
        lvl = etree.Element(Q(f"level{min(depth + 1, 6)}"))
        h = etree.SubElement(lvl, Q(f"h{min(depth + 1, 6)}"))
        h.text = f"{match.group(1)}. {match.group(2)}"
        pos = container.index(child)
        container.remove(child)
        while pos < len(container):
            candidate = container[pos]
            candidate_local = etree.QName(candidate).localname
            candidate_match = ACTIVITY.match(text(candidate)) if candidate_local == "p" else None
            if (candidate_match and len(candidate_match.group(2).strip()) > 3) or candidate_local == f"level{min(depth + 1, 6)}":
                break
            lvl.append(candidate)
        container.insert(pos, lvl)

def main():
    package = Path("9781669952961NIMAS_reconstruccion")
    path = package / "9781669952961NIMAS.xml"
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(path), parser)
    body = tree.find(f".//{Q('bodymatter')}")
    # The pass is reproducible: first restore only L02 from untouched source.
    original = etree.parse("9781669952961NIMAS_original/9781669952961NIMAS.xml", parser)
    original_body = original.find(f".//{Q('bodymatter')}")
    def section(body_element):
        children = list(body_element)
        start = next(i for i, x in enumerate(children) if etree.QName(x).localname == "level1" and pagenum(x) == 13)
        end = next(i for i, x in enumerate(children) if etree.QName(x).localname == "level1" and pagenum(x) == 25)
        return start, end
    start, end = section(body)
    for child in list(body)[start:end]:
        body.remove(child)
    original_start, original_end = section(original_body)
    for offset, child in enumerate(list(original_body)[original_start:original_end]):
        body.insert(start + offset, deepcopy(child))
    roots = list(body)
    target = next(x for x in roots if etree.QName(x).localname == "level1" and pagenum(x) == 13)
    end = next(x for x in roots if etree.QName(x).localname == "level1" and pagenum(x) == 25)
    target_index = body.index(target)
    source_roots = []
    for child in list(body)[target_index + 1:body.index(end)]:
        n = pagenum(child)
        if etree.QName(child).localname == "level1" and n is not None and 14 <= n <= 24:
            source_roots.append(child)

    # Lesson title exists as printed text on page 13; it is the sole level1 h1.
    first_text = next((x for x in target if etree.QName(x).localname == "p" and text(x) == "Lesson 2"), None)
    if first_text is not None:
        first_text.tag = Q("h1")

    # Page topics become level2 blocks in the one lesson.
    for source in source_roots:
        promote_children(source, 1, 2)
        source.tag = Q("level2")
        h1 = next((x for x in source if etree.QName(x).localname == "h1"), None)
        if h1 is not None:
            h1.tag = Q("h2")
        else:
            pg = pagenum(source)
            if pg == 16:
                heading = etree.Element(Q("h2")); heading.text = "Consonants f, r, c, d"
                source.insert(1, heading)
            elif pg == 20:
                heading = etree.Element(Q("h2")); heading.text = "Consonants f, r, c, d; Short Vowels o, i"
                source.insert(1, heading)
        body.remove(source)
        target.append(source)

    # Page 16 starts a printed review topic, but the legacy source placed it
    # inside the preceding page's C activity.  Split it into its own level2.
    topic15 = next(x for x in target if etree.QName(x).localname == "level2" and pagenum(x) == 15)
    marker16 = next(x for x in topic15 if etree.QName(x).localname == "pagenum" and text(x) == "16")
    split_at = topic15.index(marker16)
    topic16 = etree.Element(Q("level2"))
    for child in list(topic15)[split_at:]:
        topic16.append(child)
    heading = etree.Element(Q("h2")); heading.text = "Consonants f, r, c, d"
    topic16.insert(1, heading)
    target.insert(target.index(topic15) + 1, topic16)

    # The page-13 root was already the lesson root.  Promote any legacy nested
    # hierarchy under it and normalize activity labels into actual headings.
    # Only split activities directly under their topic.  Nested legacy levels
    # already have their own valid depth and must not become sibling headings.
    for topic in [x for x in target if etree.QName(x).localname == "level2"]:
        split_activities(topic, 2)

    raw = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", pretty_print=True).decode("utf-8")
    # NIMAS source requested by the publisher: line breaks retained, but never tabs/indentation.
    raw = "\n".join(line.lstrip(" \t") for line in raw.splitlines()) + "\n"
    path.write_text(raw, encoding="utf-8")

if __name__ == "__main__":
    main()
