#!/usr/bin/env python3
"""Checks proposal scope before it reaches the audit dashboard."""
import re
import subprocess
import sys
from pathlib import Path
from lxml import etree

if len(sys.argv) != 2 or not re.fullmatch(r"\d{1,2}", sys.argv[1]):
    raise SystemExit("Uso: python3 nimas-agent/validar_propuesta_leccion.py NUMERO")

lesson = int(sys.argv[1])
root = Path(__file__).resolve().parent.parent
path = root / "lecciones_propuestas" / f"L{lesson:02d}.xml"
if not path.is_file():
    raise SystemExit(f"Falta propuesta: {path}")
ns = {"d": "http://www.daisy.org/z3986/2005/dtbook/"}
tree = etree.parse(str(path))
root_node = tree.getroot()
if etree.QName(root_node).localname != "level1":
    raise SystemExit("La propuesta debe ser el fragmento level1, sin dtbook/bodymatter")
levels = [root_node]
heading = levels[0].find("d:h1", namespaces=ns)
if heading is None or " ".join(heading.itertext()).strip() != f"Lesson {lesson}":
    raise SystemExit("El level1 debe tener h1 'Lesson N'")
pages = []
for node in tree.xpath("//d:pagenum[@page='normal']", namespaces=ns):
    try: pages.append(int("".join(node.itertext()).strip()))
    except ValueError: raise SystemExit("Hay un pagenum normal no numérico")
if not pages:
    raise SystemExit("La propuesta no contiene pagenum normales")
if any(b <= a for a, b in zip(pages, pages[1:])):
    raise SystemExit("Los pagenum no están en orden creciente")
reader_panel_eight = tree.xpath(
    "//d:li[starts-with(normalize-space(string(.)), '8. Decodable Words')]",
    namespaces=ns,
)
for panel in reader_panel_eight:
    paragraphs = panel.findall("d:p", namespaces=ns)
    values = [" ".join(node.itertext()).strip() for node in paragraphs]
    if len(paragraphs) != 5 or values[:1] != ["8. Decodable Words"]:
        raise SystemExit(
            "El panel 8 de Decodable Reader debe contener cinco p: "
            "'8. Decodable Words', banco, 'High Frequency Words', Focus y Others"
        )
flat_table_choices = []
for cell in tree.xpath("//d:td", namespaces=ns):
    text = " ".join(cell.itertext())
    has_choices = re.search(r"\ba\.\s+\S+", text) and re.search(r"\bb\.\s+\S+", text)
    if has_choices and not cell.xpath("./d:list", namespaces=ns):
        flat_table_choices.append(" ".join(text.split())[:100])
if flat_table_choices:
    raise SystemExit(
        "Alternativas de selección en celda de tabla sin lista navegable: " +
        "; ".join(flat_table_choices[:3])
    )
missing = [src for src in tree.xpath("//d:img/@src", namespaces=ns)
           if not (root / "9781669952961NIMAS" / src).is_file()]
if missing:
    raise SystemExit("Imágenes inexistentes: " + ", ".join(missing[:5]))
resource_audit = root / "nimas-agent" / "auditar_recursos_sin_referenciar.py"
check = subprocess.run([sys.executable, str(resource_audit), str(lesson)],
                       cwd=root, text=True, capture_output=True)
if check.returncode:
    raise SystemExit(check.stderr.strip() or check.stdout.strip())
image_audit = root / "nimas-agent" / "auditar_asociacion_imagenes.py"
check = subprocess.run([sys.executable, str(image_audit), str(lesson)],
                       cwd=root, text=True, capture_output=True)
if check.returncode:
    raise SystemExit(check.stderr.strip() or check.stdout.strip())
print(f"L{lesson:02d}: propuesta estructuralmente apta para auditoría ({len(pages)} páginas, {len(missing)} imágenes faltantes)")
