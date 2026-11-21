#!/usr/bin/env python3
"""Flag image/list layouts that require a PDF-based association review.

This is deliberately a gate, not a blind rewriter: image order can be
editorial (one image per item) or relational (a separate matching bank).
The remediation agent must consult the PDF and then encode that relationship.
"""
import re
import sys
from pathlib import Path
from lxml import etree

if len(sys.argv) != 2 or not re.fullmatch(r"\d{1,2}", sys.argv[1]):
    raise SystemExit("Uso: python3 nimas-agent/auditar_asociacion_imagenes.py NUMERO")

lesson = int(sys.argv[1])
root = Path(__file__).resolve().parent.parent
path = root / "lecciones_propuestas" / f"L{lesson:02d}.xml"
ns = {"d": "http://www.daisy.org/z3986/2005/dtbook/"}
tree = etree.parse(str(path))

def local(node):
    return etree.QName(node).localname

issues = []
for section in tree.xpath("//d:level3", namespaces=ns):
    heading = section.find("d:h3", namespaces=ns)
    label = " ".join(heading.itertext()).strip() if heading is not None else "[sin encabezado]"
    children = list(section)
    for index, child in enumerate(children):
        if local(child) != "imggroup":
            continue
        count = len(child.xpath("./d:img", namespaces=ns))
        if count < 2:
            continue
        before = next((node for node in reversed(children[:index]) if local(node) == "list"), None)
        after = next((node for node in children[index + 1:] if local(node) == "list"), None)
        # A count mismatch does not make this safe: the extra image can be the
        # example that belongs before the exercise items.
        linked = next((node for node in (before, after) if node is not None), None)
        if linked is not None:
            direction = "después de" if linked is after else "antes de"
            item_count = len(linked.xpath("./d:li", namespaces=ns))
            issues.append(f"{label}: {count} imágenes agrupadas {direction} una lista de {item_count} ítems")

if issues:
    raise SystemExit("Revisión PDF obligatoria de asociación imagen/ítem:\n- " + "\n- ".join(issues))
print(f"L{lesson:02d}: no hay grupos imagen/lista adyacentes sin estructurar.")
