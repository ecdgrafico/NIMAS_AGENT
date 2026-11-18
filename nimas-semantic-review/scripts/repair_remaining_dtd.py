#!/usr/bin/env python3
"""Resolve the remaining validator findings without changing editorial text."""
from pathlib import Path
from lxml import etree

XML = Path("9781669952961NIMAS_corregido/9781669952961NIMAS.xml")
NS = "{http://www.daisy.org/z3986/2005/dtbook/}"


def local(node):
    return etree.QName(node).localname


tree = etree.parse(str(XML))
root = tree.getroot()

# A label inside level3 is not a level-four heading unless it opens level4.
# bridgehead retains its semantic role and is valid in DTBook content.
for heading in root.xpath('.//*[local-name()="level3"]/*[local-name()="h4"]'):
    heading.tag = NS + "bridgehead"

# Some index sections had a placeholder h2 followed by their real h2. A DTBook
# level permits only its opening h2. Transfer that existing title to the
# opening header and remove the duplicate element; no visible text is added.
for level in root.xpath('.//*[local-name()="level2"]'):
    headings = [node for node in level if local(node) == "h2"]
    if len(headings) < 2:
        continue
    first = headings[0]
    for later in headings[1:]:
        if not "".join(first.itertext()).strip():
            first.text = "".join(later.itertext())
            for key, value in later.attrib.items():
                first.set(key, value)
        level.remove(later)

etree.indent(tree, space="", level=0)
tree.write(str(XML), encoding="UTF-8", xml_declaration=True, doctype=tree.docinfo.doctype)
