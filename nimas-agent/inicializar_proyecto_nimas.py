#!/usr/bin/env python3
"""Create an isolated, review-ready NIMAS project from three local folders."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent

def package_root(path: Path) -> Path:
    candidates = [path] + [p for p in path.rglob("*") if p.is_dir()]
    for candidate in candidates:
        if any(candidate.glob("*.xml")) and (candidate / "images").is_dir():
            return candidate
    raise SystemExit(f"No encontré un paquete NIMAS (XML e images/) en: {path}")

def copy_required(source: Path, destination: Path):
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".DS_Store"))

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--original", type=Path, required=True, help="Carpeta o ZIP del paquete XML original")
parser.add_argument("--progreso", type=Path, required=True, help="Carpeta o ZIP con el progreso manual")
parser.add_argument("--pdf", type=Path, required=True, help="Carpeta con los PDF editoriales")
parser.add_argument("--destino", type=Path, required=True, help="Carpeta nueva que se va a crear")
args = parser.parse_args()

if args.destino.exists() and any(args.destino.iterdir()):
    raise SystemExit(f"El destino debe ser una carpeta nueva o vacía: {args.destino}")
if not args.pdf.is_dir() or not list(args.pdf.glob("*.pdf")):
    raise SystemExit(f"No encontré PDF en: {args.pdf}")

args.destino.mkdir(parents=True, exist_ok=True)
copy_required(package_root(args.original), args.destino / "9781669952961NIMAS_original")
copy_required(package_root(args.progreso), args.destino / "9781669952961NIMAS")
copy_required(args.pdf, args.destino / "PDF")
for relative in ("nimas-agent", "auditoria-lecciones", "nimas-semantic-review"):
    copy_required(TEMPLATE / relative, args.destino / relative)
(args.destino / "nimas-review").mkdir()
shutil.copy2(TEMPLATE / "nimas-review" / "manual-aprendizaje-agente.md", args.destino / "nimas-review")
(args.destino / "nimas-review" / "recursos_omitidos.json").write_text("{}\n", encoding="utf-8")

subprocess.run([sys.executable, "nimas-agent/split_source_lessons.py"], cwd=args.destino, check=True)
print(f"Proyecto creado: {args.destino}")
print("Inícialo con: python3 nimas-agent/servidor_auditoria.py")
