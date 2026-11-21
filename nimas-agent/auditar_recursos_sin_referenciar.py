#!/usr/bin/env python3
"""Block proposals that leave a lesson image unreviewed.

Every non-decorative image in the lesson asset folder must be referenced by
the proposal.  Explicit, documented decorative omissions live in
nimas-review/recursos_omitidos.json; this prevents a newly supplied image
from silently disappearing from the audit workflow.
"""
import json
import re
import sys
from pathlib import Path
from lxml import etree

if len(sys.argv) != 2 or not re.fullmatch(r"\d{1,2}", sys.argv[1]):
    raise SystemExit("Uso: python3 nimas-agent/auditar_recursos_sin_referenciar.py NUMERO")

lesson = int(sys.argv[1])
root = Path(__file__).resolve().parent.parent
proposal = root / "lecciones_propuestas" / f"L{lesson:02d}.xml"
assets = root / "9781669952961NIMAS" / "images" / f"L{lesson:02d}"
registry = root / "nimas-review" / "recursos_omitidos.json"
if not proposal.is_file():
    raise SystemExit(f"Falta propuesta: {proposal}")
if not assets.is_dir():
    raise SystemExit(f"Falta carpeta de imágenes: {assets}")

omitted = json.loads(registry.read_text(encoding="utf-8")) if registry.is_file() else {}
allowed = set(omitted.get(f"L{lesson:02d}", {}))
ns = {"d": "http://www.daisy.org/z3986/2005/dtbook/"}
tree = etree.parse(str(proposal))
referenced = {
    Path(src).name
    for src in tree.xpath("//d:img/@src", namespaces=ns)
    if src.startswith(f"images/L{lesson:02d}/")
}
available = {path.name for path in assets.iterdir() if path.is_file()}
pending = sorted(available - referenced - allowed)
invalid_omissions = sorted(allowed - available)
if invalid_omissions:
    raise SystemExit("Omisiones documentadas que ya no existen: " + ", ".join(invalid_omissions))
if pending:
    raise SystemExit(
        "Imágenes nuevas o sin resolver: " + ", ".join(pending) +
        ". Revísalas contra el PDF y: (1) insértalas en el XML con su relación "
        "semántica correcta, o (2) documenta una omisión decorativa justificada."
    )
print(f"L{lesson:02d}: todos los recursos de imagen están referenciados o documentados.")
