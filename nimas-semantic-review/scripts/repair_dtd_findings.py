#!/usr/bin/env python3
"""Repair mechanical DTBook 2005-3 violations reported by NIMAS validation."""
from pathlib import Path
from lxml import etree

PACKAGE = Path("9781669952961NIMAS_corregido")
XML = PACKAGE / "9781669952961NIMAS.xml"
NS = "{http://www.daisy.org/z3986/2005/dtbook/}"


def name(node):
    return etree.QName(node).localname


def prepend(parent, node):
    parent.insert(0, node)


tree = etree.parse(str(XML))
root = tree.getroot()

# The validator requires an IDREF, not a filename, in caption/@imgref.
images = {node.get("src"): node.get("id") for node in root.xpath('.//*[local-name()="img"]')}
for caption in root.xpath('.//*[local-name()="caption"][@imgref]'):
    value = caption.get("imgref")
    if value in images and images[value]:
        caption.set("imgref", images[value])

# An imggroup cannot be empty. Empty groups contain no editorial material and
# were artifacts of the image-path substitution, so remove only those.
for group in list(root.xpath('.//*[local-name()="imggroup"]')):
    if not any(name(child) in {"prodnote", "img", "caption", "pagenum"} for child in group):
        group.getparent().remove(group)

# A DTBook level needs its matching heading and some following content. Empty
# headings/paragraphs are structural placeholders only; no reader-visible text
# is introduced.
for level_tag, heading_tag in [("level2", "h2"), ("level3", "h3"), ("level4", "h4"), ("level5", "h5"), ("level6", "h6")]:
    for level in list(root.xpath(f'.//*[local-name()="{level_tag}"]')):
        children = list(level)
        if not children or name(children[0]) != heading_tag:
            heading = etree.Element(NS + heading_tag)
            prepend(level, heading)
            children = list(level)
        if len(children) == 1:
            level.append(etree.Element(NS + "p"))

# Consecutive accidental level3 nesting is invalid. Preserve their content as
# a legitimate next depth level, including the matching header tag.
for old, new, h_old, h_new in [("level3", "level4", "h3", "h4"), ("level4", "level5", "h4", "h5"), ("level5", "level6", "h5", "h6")]:
    for level in list(root.xpath(f'.//*[local-name()="{old}"]/*[local-name()="{old}"]')):
        level.tag = NS + new
        for heading in level.xpath(f'./*[local-name()="{h_old}"]'):
            heading.tag = NS + h_new

# A level that starts with a lower level must have an empty matching heading.
for level_tag, heading_tag in [("level2", "h2"), ("level3", "h3"), ("level4", "h4"), ("level5", "h5"), ("level6", "h6")]:
    for level in root.xpath(f'.//*[local-name()="{level_tag}"]'):
        if not len(level) or name(level[0]) != heading_tag:
            prepend(level, etree.Element(NS + heading_tag))

etree.indent(tree, space="", level=0)
tree.write(str(XML), encoding="UTF-8", xml_declaration=True, doctype=tree.docinfo.doctype)

# Finder metadata is not a NIMAS resource and must not enter the archive.
for file in PACKAGE.rglob('.DS_Store'):
    file.unlink()
