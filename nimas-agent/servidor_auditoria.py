#!/usr/bin/env python3
"""Local project server for the NIMAS audit dashboard.

It exposes project discovery, on-demand PDF rendering, and an explicit queue
for proposal generation. It never installs a proposal into the NIMAS package.
"""
import json
import os
import re
import hashlib
import subprocess
import sys
import threading
from datetime import datetime
import shutil
import tempfile
import mimetypes
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from lxml import etree
from library import all_projects, register, rename_project, remove_project
from project_data import load_project, save_project
from ai_provider import provider_status, write_prompt
from pypdf import PdfReader

APP_ROOT = Path(__file__).resolve().parent.parent
ROOT = Path(os.environ.get("NIMAS_PROJECT_ROOT", APP_ROOT)).resolve()
LIBRARY_ROOT = Path(os.environ.get("NIMAS_LIBRARY_ROOT", APP_ROOT / "nimas-library")).resolve()
LIBRARY_DB = LIBRARY_ROOT / "library.db"
FRONTEND_DIST = APP_ROOT / "frontend-vue" / "dist"
NS = {"d": "http://www.daisy.org/z3986/2005/dtbook/"}
JOBS = {"running": False, "lesson": None, "queue": [], "log": "", "events": [], "followups": [], "stage": None, "startedAt": None, "export": None}
LOCK = threading.Lock()

def pages(path):
    # Some original lesson fragments retain adjacent level1 nodes and are not
    # standalone XML documents. Page anchors are still reliable text markers.
    raw = path.read_text(encoding="utf-8", errors="replace")
    values = [int(value) for value in re.findall(
        r'<pagenum\b[^>]*\bpage=["\']normal["\'][^>]*>\s*(\d+)\s*</pagenum>', raw, re.I
    )]
    return (min(values), max(values)) if values else (None, None)

def approved():
    record = ROOT / "nimas-review" / "registro-aprobaciones.md"
    return {int(value) for value in re.findall(r"\| L(\d{2}) \|[^|]*\| Aprobada", record.read_text(encoding="utf-8") if record.is_file() else "")}

def approved_editorial():
    record = ROOT / "nimas-review" / "registro-aprobaciones.md"
    text = record.read_text(encoding="utf-8") if record.is_file() else ""
    return set(re.findall(r"\| (FM|EM) \|[^|]*\| Aprobada", text))

def project_status():
    if ROOT.resolve() == APP_ROOT.resolve():
        return {"ready": False, "active": False, "name": None, "mode": None}
    if (ROOT / "project.yaml").is_file():
        raw = (ROOT / "project.yaml").read_text(encoding="utf-8", errors="replace")
        mode = "nimas_zip" if "source_mode: nimas_zip" in raw else "pdf_only"
        return {"ready": True, "active": True, "name": ROOT.name, "mode": mode, "projectRoot": str(ROOT)}
    required = ["lecciones_originales", "PDF", "9781669952961NIMAS", "9781669952961NIMAS_original"]
    ready = all((ROOT / path).exists() for path in required)
    return {"ready": ready, "active": ready, "name": ROOT.name if ready else None}

def library_projects():
    return {"projects": all_projects(LIBRARY_DB)}

def range_audits():
    check = subprocess.run([sys.executable, "nimas-agent/auditar_rangos_editoriales.py"], cwd=ROOT, text=True, capture_output=True)
    try:
        return json.loads(check.stdout) if check.returncode == 0 else {}
    except json.JSONDecodeError:
        return {}

def lessons():
    result = []
    audits = range_audits()
    for original in sorted((ROOT / "lecciones_originales").glob("L[0-9][0-9].xml")):
        number = int(original.stem[1:])
        first, last = pages(original)
        proposal = ROOT / "lecciones_propuestas" / original.name
        pdfs = list((ROOT / "PDF").glob(f"*L{number:02d}_*.pdf"))
        recovery = audits.get(f"L{number:02d}", {})
        status = "reference" if number <= 3 else "approved" if number in approved() else "recovery_ready" if recovery.get("required") and proposal.is_file() else "recovery" if recovery.get("required") else "ready" if proposal.is_file() else "pending"
        display_first, display_last = recovery.get("expected", [first, last]) if recovery.get("required") else (first, last)
        result.append({"lesson": number, "first": display_first, "last": display_last, "sourceFirst": first, "sourceLast": last, "status": status,
                       "pdf": f"../PDF/{pdfs[0].name}" if pdfs else None, "recovery": recovery,
                       "hasProposal": proposal.is_file()})
    return result

def editorial_sections():
    if (ROOT / "project.yaml").is_file():
        return []
    if not project_status()["ready"]:
        return []
    audits = range_audits()
    fm = ROOT / "lecciones_originales" / "FM.xml"
    em = ROOT / "lecciones_originales" / "EM.xml"
    fm_raw = fm.read_text(encoding="utf-8", errors="replace") if fm.is_file() else ""
    fm_pages = re.findall(r'<pagenum\b[^>]*>\s*([^<]+)', fm_raw, re.I)
    em_audit = audits.get("EM", {})
    editorial_approved = approved_editorial()
    return [
        {"key": "FM", "name": "FM · Frontmatter", "pdf": "../PDF/PHE27_SE_FM_i-iv_hi.pdf",
         "status": "approved" if "FM" in editorial_approved else "recovery", "approved": "FM" in editorial_approved, "pages": "i–vii", "sourcePages": ", ".join(fm_pages),
         "reason": "La propuesta cubre todo el contenido editorial i–vii; viii es una página final en blanco y se omite."},
        {"key": "EM", "name": "EM · Rearmatter", "pdf": "../PDF/PHE27_SE_EM_287-304_hi.pdf",
         "status": "approved" if "EM" in editorial_approved else "recovery", "approved": "EM" in editorial_approved, "pages": "287–297", "sourcePages": "278–295",
         "reason": "La propuesta corrige el desfase de nueve folios del XML fuente, conserva el contenido visible 287–297 y omite las páginas finales en blanco 298–304."},
    ]

def editorial_pages(key):
    return ["i", "ii", "iii", "iv", "v", "vi", "vii"] if key == "FM" else [str(page) for page in range(287, 298)]

def validate_editorial_proposal(key):
    proposal = ROOT / "secciones_propuestas" / f"{key}.xml"
    if not proposal.is_file():
        raise ValueError(f"No existe propuesta para {key}")
    raw = proposal.read_text(encoding="utf-8")
    try:
        root = etree.fromstring(f'<root xmlns="{NS["d"]}">{raw}</root>'.encode("utf-8"))
    except etree.XMLSyntaxError as error:
        raise ValueError(f"La propuesta de {key} no es XML bien formado: {error}") from error
    pages_found = ["".join(node.itertext()).strip() for node in root.iter(f'{{{NS["d"]}}}pagenum')]
    expected = editorial_pages(key)
    if pages_found != expected:
        raise ValueError(f"{key} debe contener exactamente las páginas {', '.join(expected)}; se encontraron {', '.join(pages_found) or 'ninguna'}.")
    headings = [" ".join("".join(node.itertext()).split()) for node in root.iter(f'{{{NS["d"]}}}h1')]
    if key == "FM":
        if not root.findall(f'{{{NS["d"]}}}doctitle') or not root.findall(f'{{{NS["d"]}}}docauthor'):
            raise ValueError("FM debe conservar doctitle y docauthor.")
    else:
        if headings[:2] != ["CREDITS", "INDEX"]:
            raise ValueError("EM debe iniciar sus unidades con los h1 Credits e Index.")
        if list(root.iter(f'{{{NS["d"]}}}img')):
            raise ValueError("EM no debe incluir imágenes para sus páginas finales en blanco.")

def render_editorial(key):
    item = next((section for section in editorial_sections() if section["key"] == key), None)
    if not item:
        raise ValueError("Sección desconocida")
    output = ROOT / "auditoria-lecciones" / "assets" / key
    output.mkdir(parents=True, exist_ok=True)
    count = len(editorial_pages(key))
    if len(list(output.glob("page-*.png"))) < count:
        source = ROOT / item["pdf"].removeprefix("../")
        subprocess.run(["pdftoppm", "-png", "-r", "150", str(source), str(output / "page")], check=True)
        for image in output.glob("page-*.png"):
            match = re.search(r"-(\d+)\.png$", image.name)
            if match:
                image.rename(output / f"page-{int(match.group(1)):02d}.png")

def editorial_images(key, page):
    proposal = ROOT / "secciones_propuestas" / f"{key}.xml"
    if not proposal.is_file():
        return []
    raw = proposal.read_text(encoding="utf-8", errors="replace")
    marker = re.compile(rf'<pagenum\b[^>]*>\s*{re.escape(page)}\s*</pagenum>', re.I)
    found = marker.search(raw)
    if not found:
        return []
    next_marker = re.search(r'<pagenum\b', raw[found.end():], re.I)
    fragment = raw[found.end(): found.end() + next_marker.start() if next_marker else len(raw)]
    result = []
    for attrs in re.findall(r'<img\b([^>]+)/?>', fragment, re.I):
        src = re.search(r'\bsrc=["\']([^"\']+)', attrs)
        if not src:
            continue
        asset = (ROOT / "9781669952961NIMAS" / src.group(1)).resolve()
        package = (ROOT / "9781669952961NIMAS" / "images").resolve()
        if package not in asset.parents or not asset.is_file():
            continue
        ident = re.search(r'\bid=["\']([^"\']+)', attrs)
        result.append({"id": ident.group(1) if ident else "", "src": src.group(1), "url": "/9781669952961NIMAS/" + src.group(1)})
    return result

def render(number):
    entry = next((item for item in lessons() if item["lesson"] == number), None)
    if not entry or not entry["pdf"]:
        raise ValueError("No hay PDF asociado a esa lección")
    output = ROOT / "auditoria-lecciones" / "assets" / f"L{number:02d}"
    output.mkdir(parents=True, exist_ok=True)
    expected = entry["last"] - entry["first"] + 1
    if len(list(output.glob("page-*.png"))) < expected:
        source = ROOT / entry["pdf"].removeprefix("../")
        subprocess.run(["pdftoppm", "-png", "-r", "150", str(source), str(output / "page")], check=True)
        for image in output.glob("page-*.png"):
            match = re.search(r"-(\d+)\.png$", image.name)
            if match:
                image.rename(output / f"page-{int(match.group(1)):02d}.png")

def proposal_images(number, page):
    """Return only the image assets anchored after this editorial page."""
    proposal = ROOT / "lecciones_propuestas" / f"L{number:02d}.xml"
    if not proposal.is_file():
        return []
    root = etree.parse(str(proposal)).getroot()
    current_page = None
    found = []
    for node in root.iter():
        if etree.QName(node).localname == "pagenum" and "".join(node.itertext()).strip().isdigit():
            current_page = int("".join(node.itertext()).strip())
        if etree.QName(node).localname != "img" or current_page != page:
            continue
        src = node.get("src", "")
        asset = (ROOT / "9781669952961NIMAS" / src).resolve()
        package = (ROOT / "9781669952961NIMAS" / "images").resolve()
        if not src or package not in asset.parents or not asset.is_file():
            continue
        group = node.getparent()
        captions = ["".join(c.itertext()).strip() for c in group if etree.QName(c).localname == "caption"] if group is not None else []
        found.append({"id": node.get("id", ""), "src": src, "caption": " ".join(x for x in captions if x),
                      "url": "/9781669952961NIMAS/" + src})
    return found

def project_unit(unit_id):
    units = load_project(ROOT).get("structure", {}).get("units", [])
    return next((unit for unit in units if str(unit.get("id")) == str(unit_id)), None)

def proposal_page_fragment(raw, page):
    """Return the evidence window for one PDF page, never the full proposal."""
    if not raw:
        return None
    marker = re.compile(r"<pagenum\b[^>]*>\s*" + re.escape(str(page)) + r"\s*</pagenum>", re.I)
    found = marker.search(raw)
    if not found:
        return None
    next_page = re.search(r"<pagenum\b", raw[found.end():], re.I)
    end = found.end() + next_page.start() if next_page else len(raw)
    return raw[found.start():end].strip()

def unit_detail(unit_id, requested_page=None):
    unit = project_unit(unit_id)
    if not unit:
        raise ValueError("Unidad no encontrada")
    source = ROOT / "fuentes" / "pdf" / str(unit.get("file", ""))
    if not source.is_file():
        source = ROOT / "fuentes" / "pdf" / Path(str(unit.get("file", ""))).name
    pages = unit.get("pages") or [1, 0]
    proposal = ROOT / "propuestas" / f"{unit_id}.xml"
    source_xml = None
    # ZIP projects may expose a source XML either explicitly in the unit
    # record or under the conventional source folders. Never mutate it.
    candidates = []
    if unit.get("xml"):
        candidates.append(ROOT / str(unit["xml"]))
    if unit.get("source_xml"):
        candidates.append(ROOT / str(unit["source_xml"]))
    candidates.extend([
        ROOT / "lecciones_originales" / f"{unit_id}.xml",
        ROOT / "fuentes" / "xml" / f"{unit_id}.xml",
        ROOT / "xml" / f"{unit_id}.xml",
    ])
    for candidate in candidates:
        if candidate.is_file() and (ROOT in candidate.resolve().parents or candidate.resolve() == ROOT):
            source_xml = candidate.read_text(encoding="utf-8", errors="replace")
            break
    assets_path = ROOT / "inventario" / "images.json"
    assets = json.loads(assets_path.read_text(encoding="utf-8")) if assets_path.is_file() else {"assets": []}
    selected_assets = []
    try:
        printed_first = int(pages[0])
        printed_last = int(pages[1])
    except (TypeError, ValueError):
        printed_first, printed_last = 1, 0
    for asset in assets.get("assets", []):
        candidates = asset.get("candidate_units", [])
        same_pdf = Path(str(asset.get("source_pdf", ""))).name == Path(str(unit.get("file", ""))).name
        physical_page = int(asset.get("page", 0) or 0)
        in_unit = printed_first <= physical_page + printed_first - 1 <= printed_last
        if str(unit_id) in candidates or (same_pdf and in_unit):
            selected_assets.append({**asset, "display_page": physical_page + printed_first - 1,
                                    "url": "/working/detected-images/" + str(asset.get("file", ""))})
    decisions_path = ROOT / "revision" / "page-decisions.json"
    decisions = json.loads(decisions_path.read_text(encoding="utf-8")) if decisions_path.is_file() else {}
    proposal_text = proposal.read_text(encoding="utf-8", errors="replace") if proposal.is_file() else None
    proposal_page = proposal_page_fragment(proposal_text, requested_page if requested_page is not None else (pages[0] if pages else None)) if proposal_text and pages else None
    provider = None
    runs = ROOT / "versions" / "ai-runs"
    for candidate in ("ollama", "codex"):
        if (runs / f"{unit_id}-{candidate}.md").is_file():
            provider = candidate
            break
    project_yaml = ROOT / "project.yaml"
    source_mode = "pdf_only" if project_yaml.is_file() and "source_mode: pdf_only" in project_yaml.read_text(encoding="utf-8", errors="replace") else "nimas_zip"
    return {"unit": unit, "mode": source_mode, "provider": provider, "pdf": str(source.relative_to(ROOT)).replace("\\", "/") if source.is_file() else None,
            "pages": pages, "source": source_xml,
            "proposal": proposal_text, "proposal_page": proposal_page,
            "assets": selected_assets, "hasProposal": proposal.is_file(), "decisions": decisions.get(str(unit_id), {})}

def render_unit(unit_id, page):
    detail = unit_detail(unit_id)
    source = ROOT / str(detail["pdf"] or "")
    if not source.is_file():
        raise ValueError("PDF de la unidad no encontrado")
    output = ROOT / "working" / "unit-pages" / re.sub(r"[^A-Za-z0-9_-]+", "_", str(unit_id))
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"page-{int(page):04d}.png"
    if not target.is_file():
        import fitz
        with fitz.open(str(source)) as document:
            try:
                printed_first = int(detail["pages"][0])
            except (TypeError, ValueError):
                printed_first = 1
            index = int(page) - printed_first
            if index < 0 or index >= len(document):
                raise ValueError("Página fuera del rango del PDF")
            pixmap = document[index].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            pixmap.save(str(target))
    return "/working/unit-pages/" + re.sub(r"[^A-Za-z0-9_-]+", "_", str(unit_id)) + f"/page-{int(page):04d}.png"

def adjustment_path(number, page):
    folder = ROOT / "nimas-review" / "solicitudes-ajuste"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"L{number:02d}-p{page:03d}.md"

def adjustment_report(number):
    entry = next(item for item in lessons() if item["lesson"] == number)
    adjustment_dir = ROOT / "nimas-review" / "solicitudes-ajuste"
    notes = sorted(adjustment_dir.glob(f"L{number:02d}-p*.md")) if adjustment_dir.is_dir() else []
    text = [f"# Informe editorial · Lección {number:02d}", "",
            f"- Páginas: {entry['first']}–{entry['last']}",
            f"- Estado: {entry['status']}",
            f"- Propuesta: `lecciones_propuestas/L{number:02d}.xml`", "",
            "## Reglas aplicadas", "",
            "La fuente normativa es `nimas-review/manual-aprendizaje-agente.md`. "
            "La propuesta debe conservar un único `level1`, cotejar cada página con el PDF, "
            "usar estructura semántica para listas/tablas y asociar cada imagen al ítem o ejemplo correspondiente.", "",
            "## Solicitudes editoriales registradas", ""]
    if notes:
        for note in notes:
            text += [f"### {note.stem}", "", note.read_text(encoding="utf-8").strip(), ""]
    else:
        text += ["No hay solicitudes adicionales registradas.", ""]
    text += ["## Prompt de implementación", "",
             f"Revisar L{number:02d} con el PDF, el XML original y el manual. Aplicar las solicitudes anteriores sin modificar la fuente ni una lección aprobada. "
             "Generar una propuesta completa, validar XML/DTD y verificar recursos y asociación imagen/ítem antes de presentarla a auditoría.", ""]
    return "\n".join(text)

def run_queue(numbers):
    with LOCK:
        JOBS.update(running=True, queue=numbers[:], log="", stage="Preparando fuentes y reglas", startedAt=datetime.now().isoformat())
    try:
        for number in numbers:
            with LOCK: JOBS.update(lesson=number, queue=[n for n in numbers if n > number], stage="Analizando PDF, XML y reglas editoriales")
            proposal = ROOT / "lecciones_propuestas" / f"L{number:02d}.xml"
            if proposal.is_file():
                history = ROOT / "nimas-review" / "historial-propuestas" / f"L{number:02d}"
                history.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                shutil.copy2(proposal, history / f"{stamp}-antes-de-regenerar.xml")
            process = subprocess.run(["zsh", "nimas-agent/generar_propuesta_leccion.sh", str(number)], cwd=ROOT, text=True, capture_output=True)
            with LOCK: JOBS["log"] += f"\nL{number:02d}\n{process.stdout}{process.stderr}"
            with LOCK:
                JOBS["events"].append({"lesson": number, "ok": process.returncode == 0,
                                       "message": f"L{number:02d}: nueva propuesta lista para revisión." if process.returncode == 0 else f"L{number:02d}: la regeneración requiere revisión técnica."})
            if process.returncode:
                break
    finally:
        with LOCK:
            followups = list(dict.fromkeys(JOBS["followups"]))
            JOBS.update(running=False, lesson=None, followups=[], stage=None, startedAt=None)
        if followups:
                threading.Thread(target=run_queue, args=(followups,), daemon=True).start()

def run_page_adjustment(number, page):
    with LOCK:
        JOBS.update(running=True, lesson=number, queue=[f"L{number:02d}/p{page}"], log="", stage=f"Corrigiendo solo la página {page}", startedAt=datetime.now().isoformat())
    try:
        proposal = ROOT / "lecciones_propuestas" / f"L{number:02d}.xml"
        if not proposal.is_file():
            raise ValueError("No existe propuesta previa para corregir por página")
        history = ROOT / "nimas-review" / "historial-propuestas" / f"L{number:02d}"
        history.mkdir(parents=True, exist_ok=True)
        shutil.copy2(proposal, history / f"{datetime.now():%Y%m%d-%H%M%S}-antes-de-p{page:03d}.xml")
        process = subprocess.run(["zsh", "nimas-agent/generar_propuesta_leccion.sh", str(number), str(page)], cwd=ROOT, text=True, capture_output=True)
        with LOCK:
            JOBS["log"] += f"\nL{number:02d}/p{page}\n{process.stdout}{process.stderr}"
            JOBS["events"].append({"lesson": number, "page": page, "ok": process.returncode == 0,
                "message": f"L{number:02d}, página {page}: ajuste listo para revisión." if process.returncode == 0 else f"L{number:02d}, página {page}: el ajuste requiere revisión técnica."})
    except Exception as error:
        with LOCK: JOBS["events"].append({"lesson": number, "page": page, "ok": False, "message": str(error)})
    finally:
        with LOCK: JOBS.update(running=False, lesson=None, queue=[], stage=None, startedAt=None)

def run_editorial_section(key):
    with LOCK:
        JOBS.update(running=True, lesson=key, queue=[key], log="", stage="Reconstruyendo desde PDF y cotejando XML", startedAt=datetime.now().isoformat())
    try:
        proposal = ROOT / "secciones_propuestas" / f"{key}.xml"
        if proposal.is_file():
            history = ROOT / "nimas-review" / "historial-propuestas" / key
            history.mkdir(parents=True, exist_ok=True)
            shutil.copy2(proposal, history / f"{datetime.now():%Y%m%d-%H%M%S}-antes-de-regenerar.xml")
        process = subprocess.run(["zsh", "nimas-agent/generar_propuesta_seccion.sh", key], cwd=ROOT, text=True, capture_output=True)
        with LOCK:
            JOBS["log"] += f"\n{key}\n{process.stdout}{process.stderr}"
            JOBS["events"].append({"lesson": key, "ok": process.returncode == 0,
                "message": f"{key}: nueva propuesta lista para auditoría." if process.returncode == 0 else f"{key}: la reconstrucción requiere revisión técnica."})
    finally:
        with LOCK: JOBS.update(running=False, lesson=None, queue=[], stage=None, startedAt=None)

def run_export():
    """Build a new package only from approved proposals; never alters sources."""
    with LOCK:
        JOBS.update(running=True, lesson="ZIP NIMAS", queue=["ZIP"], log="", stage="Ensamblando XML aprobado y reconstruyendo el manifiesto OPF", startedAt=datetime.now().isoformat(), export=None)
    try:
        exporter = "nimas-agent/export_pdf_project.py" if (ROOT / "project.yaml").is_file() else "nimas-agent/exportar_paquete_nimas.py"
        command = [sys.executable, exporter]
        if exporter.endswith("export_pdf_project.py"): command += ["--project", str(ROOT)]
        process = subprocess.run(command, cwd=ROOT if exporter.endswith("exportar_paquete_nimas.py") else APP_ROOT, text=True, capture_output=True)
        output = (process.stdout or "").strip()
        with LOCK:
            JOBS["log"] += f"\nEXPORTACIÓN\n{output}\n{process.stderr}"
        result = json.loads(output.splitlines()[-1]) if output else {}
        if process.returncode or result.get("status") != "pass":
            raise ValueError(result.get("error") or process.stderr.strip() or "La validación del paquete no fue satisfactoria")
        with LOCK:
            JOBS["export"] = result
            JOBS["events"].append({"lesson": "ZIP", "ok": True, "message": "ZIP NIMAS validado y listo para descargar.", "export": result})
    except Exception as error:
        with LOCK:
            JOBS["events"].append({"lesson": "ZIP", "ok": False, "message": f"No se creó el ZIP: {error}"})
    finally:
        with LOCK: JOBS.update(running=False, lesson=None, queue=[], stage=None, startedAt=None)

def run_assets():
    with LOCK:
        JOBS.update(running=True, lesson="IMÁGENES", queue=["IMÁGENES"], log="", stage="Analizando PDF y extrayendo imágenes", startedAt=datetime.now().isoformat())
    try:
        process = subprocess.run([sys.executable, "nimas-agent/detect_pdf_assets.py", "--project", str(ROOT)], cwd=APP_ROOT, text=True, capture_output=True)
        with LOCK:
            JOBS["log"] += f"\nIMÁGENES\n{process.stdout}{process.stderr}"
            if process.returncode == 0:
                result = json.loads(process.stdout.splitlines()[-1])
                JOBS["events"].append({"lesson":"IMÁGENES", "ok":True, "message":f"Recursos visuales detectados: {result.get('count',0)}."})
            else:
                JOBS["events"].append({"lesson":"IMÁGENES", "ok":False, "message":process.stderr.strip() or "Falló el análisis de imágenes."})
    finally:
        with LOCK: JOBS.update(running=False, lesson=None, queue=[], stage=None, startedAt=None)

def run_ai_proposal(unit_id, provider="codex"):
    with LOCK: JOBS.update(running=True, lesson=unit_id, queue=[unit_id], log="", stage=f"Generando propuesta DTBook con {provider}", startedAt=datetime.now().isoformat())
    try:
        assets=subprocess.run([sys.executable,"nimas-agent/detect_pdf_assets.py","--project",str(ROOT),"--unit",unit_id],cwd=APP_ROOT,text=True,capture_output=True)
        process=subprocess.run([sys.executable,"nimas-agent/generate_ai_proposal.py","--project",str(ROOT),"--unit",unit_id,"--provider",provider],cwd=APP_ROOT,text=True,capture_output=True)
        with LOCK:
            JOBS["log"]+=f"\nIMÁGENES DE UNIDAD\n{assets.stdout}{assets.stderr}\n{process.stdout}{process.stderr}"
            JOBS["events"].append({"lesson":unit_id,"ok":process.returncode==0,"message":process.stdout.strip() if process.returncode==0 else process.stderr.strip() or "La propuesta requiere revisión técnica."})
    finally:
        with LOCK: JOBS.update(running=False,lesson=None,queue=[],stage=None,startedAt=None)

def run_ai_all(provider="codex"):
    units=load_project(ROOT).get('structure',{}).get('units',[])
    ids=[str(unit.get('id','')) for unit in units]
    with LOCK: JOBS.update(running=True,lesson="LIBRO",queue=ids.copy(),log="",stage=f"Generando {len(ids)} propuestas DTBook",startedAt=datetime.now().isoformat())
    try:
        for position,unit_id in enumerate(ids):
            with LOCK: JOBS.update(lesson=unit_id,queue=ids[position:],stage=f"Generando propuesta {unit_id}")
            assets=subprocess.run([sys.executable,"nimas-agent/detect_pdf_assets.py","--project",str(ROOT),"--unit",unit_id],cwd=APP_ROOT,text=True,capture_output=True)
            process=subprocess.run([sys.executable,"nimas-agent/generate_ai_proposal.py","--project",str(ROOT),"--unit",unit_id,"--provider",provider],cwd=APP_ROOT,text=True,capture_output=True)
            with LOCK:
                JOBS["log"]+=f"\nIMÁGENES DE UNIDAD\n{assets.stdout}{assets.stderr}\n{process.stdout}{process.stderr}"
                JOBS["events"].append({"lesson":unit_id,"ok":process.returncode==0,"message":process.stdout.strip() if process.returncode==0 else process.stderr.strip() or "La propuesta requiere revisión técnica."})
    finally:
        with LOCK: JOBS.update(running=False,lesson=None,queue=[],stage=None,startedAt=None)

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        if os.environ.get("NIMAS_VERBOSE") == "1":
            super().log_message(format, *args)

    def translate_path(self, path):
        relative = Path(urlparse(path).path.lstrip("/"))
        base = APP_ROOT if relative.parts and relative.parts[0] == "auditoria-lecciones" else ROOT
        target = (base / relative).resolve()
        return str(target if base in target.parents or target == base else base)
    def json(self, value, status=200):
        payload = json.dumps(value).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)
    def multipart_fields(self):
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise ValueError("Selecciona uno o más archivos PDF")
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        message = BytesParser(policy=policy.default).parsebytes((f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
        fields, files = {}, []
        for part in message.iter_parts():
            disposition = part.get("Content-Disposition", "")
            params = dict(part.get_params(header="Content-Disposition", unquote=True))
            name = params.get("name")
            filename = params.get("filename")
            if filename:
                files.append((filename, part.get_payload(decode=True) or b""))
            elif name:
                fields[name] = part.get_content()
        return fields, files
    def serve_frontend(self, path):
        """Serve the built Vue SPA and fall back to index.html for client routes."""
        if not FRONTEND_DIST.is_dir():
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "frontend-vue/dist no existe; ejecuta npm run build")
            return
        relative = Path(urlparse(path).path.lstrip("/"))
        target = (FRONTEND_DIST / relative).resolve()
        if FRONTEND_DIST not in target.parents or not target.is_file():
            target = FRONTEND_DIST / "index.html"
        payload = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(str(target))[0] or "application/octet-stream")
        self.send_header("Cache-Control", "no-cache" if target.name == "index.html" else "public, max-age=31536000, immutable")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/nimac-template":
            template = APP_ROOT / "nimas-agent" / "nimac_metadata_template.json"
            return self.json(json.loads(template.read_text(encoding="utf-8")))
        if parsed.path == "/api/project-status": return self.json(project_status())
        if parsed.path == "/api/provider-status": return self.json(provider_status())
        if parsed.path == "/api/project-detail": return self.json(load_project(ROOT))
        if parsed.path == "/api/project-units": return self.json({"units": load_project(ROOT).get("structure", {}).get("units", [])})
        if parsed.path == "/api/unit-detail":
            try:
                unit = parse_qs(parsed.query).get("unit", [""])[0]
                requested_page = parse_qs(parsed.query).get("page", [None])[0]
                return self.json(unit_detail(unit, requested_page))
            except Exception as error: return self.json({"error": str(error)}, 404)
        if parsed.path == "/api/unit-render":
            try:
                unit = parse_qs(parsed.query).get("unit", [""])[0]
                page = parse_qs(parsed.query).get("page", ["1"])[0]
                return self.json({"url": render_unit(unit, page)})
            except Exception as error: return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/project-preflight":
            process=subprocess.run([sys.executable,str(APP_ROOT/"nimas-agent"/"preflight_project.py"),"--project",str(ROOT)],cwd=APP_ROOT,text=True,capture_output=True)
            try: return self.json(json.loads(process.stdout.splitlines()[-1]))
            except Exception: return self.json({"status":"error","message":process.stderr.strip() or process.stdout.strip()},500)
        if parsed.path == "/api/project-assets":
            path = ROOT / "inventario" / "images.json"
            return self.json(json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"count": 0, "assets": []})
        if parsed.path == "/api/proposal-validation":
            unit = parse_qs(parsed.query).get("unit", [""])[0]
            report = ROOT / "versions" / "ai-runs" / f"{unit}-validation.json"
            result = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else {"status": "pending", "errors": []}
            result["text_fallback"] = (ROOT / "versions" / "ai-runs" / f"{unit}-fallback.md").is_file()
            return self.json(result)
        if parsed.path == "/api/projects": return self.json(library_projects())
        if parsed.path == "/api/lessons": return self.json({"lessons": lessons()})
        if parsed.path == "/api/editorial-sections": return self.json({"sections": editorial_sections()})
        if parsed.path == "/api/editorial-detail":
            key = parse_qs(parsed.query).get("section", [""])[0].upper()
            item = next((x for x in editorial_sections() if x["key"] == key), None)
            if not item: return self.json({"error": "Sección desconocida"}, 404)
            source = ROOT / "lecciones_originales" / f"{key}.xml"
            proposal = ROOT / "secciones_propuestas" / f"{key}.xml"
            return self.json({**item, "pageIds": editorial_pages(key), "source": source.read_text(encoding="utf-8", errors="replace"), "proposal": proposal.read_text(encoding="utf-8", errors="replace") if proposal.is_file() else None})
        if parsed.path == "/api/editorial-render":
            try:
                key = parse_qs(parsed.query).get("section", [""])[0].upper()
                render_editorial(key)
                return self.json({"ok": True})
            except Exception as error: return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/editorial-images":
            try:
                key = parse_qs(parsed.query).get("section", [""])[0].upper()
                page = parse_qs(parsed.query).get("page", [""])[0]
                return self.json({"images": editorial_images(key, page)})
            except Exception as error: return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/job":
            with LOCK: return self.json(JOBS)
        if parsed.path == "/api/render":
            try:
                render(int(parse_qs(parsed.query).get("lesson", [""])[0])); return self.json({"ok": True})
            except Exception as error: return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/page-images":
            try:
                number = int(parse_qs(parsed.query).get("lesson", [""])[0])
                page = int(parse_qs(parsed.query).get("page", [""])[0])
                return self.json({"images": proposal_images(number, page)})
            except Exception as error: return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/report":
            try:
                number = int(parse_qs(parsed.query).get("lesson", [""])[0])
                payload = adjustment_report(number).encode()
                self.send_response(200); self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="informe-L{number:02d}.md"')
                self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload); return
            except Exception as error: return self.json({"error": str(error)}, 400)
        if parsed.path == "/" or (not parsed.path.startswith("/api/") and not parsed.path.startswith("/auditoria-lecciones") and not parsed.path.startswith("/working/")):
            return self.serve_frontend(parsed.path)
        return super().do_GET()
    def do_POST(self):
        global ROOT
        parsed = urlparse(self.path); query = parse_qs(parsed.query)
        if parsed.path == "/api/open-project":
            try:
                size = int(self.headers.get("Content-Length", "0")); data = json.loads(self.rfile.read(size))
                selected = Path(str(data.get("path", ""))).resolve()
                library_projects_root = (LIBRARY_ROOT / "projects").resolve()
                if library_projects_root not in selected.parents or not (selected / "project.yaml").is_file():
                    raise ValueError("Proyecto no válido en la biblioteca")
                ROOT = selected
                os.environ["NIMAS_PROJECT_ROOT"] = str(selected)
                return self.json({"ok": True, "name": selected.name, "path": str(selected)})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/close-project":
            ROOT = APP_ROOT.resolve()
            os.environ.pop("NIMAS_PROJECT_ROOT", None)
            with LOCK:
                if not JOBS["running"]: JOBS.update(lesson=None, queue=[], stage=None, export=None)
            return self.json({"ok": True, "message": "Proyecto cerrado. Biblioteca activa."})
        if parsed.path == "/api/rename-project":
            try:
                size = int(self.headers.get("Content-Length", "0")); data = json.loads(self.rfile.read(size))
                selected = Path(str(data.get("path", ""))).resolve(); name = str(data.get("name", "")).strip()
                library_projects_root = (LIBRARY_ROOT / "projects").resolve()
                if library_projects_root not in selected.parents or not (selected / "project.yaml").is_file(): raise ValueError("Proyecto no válido en la biblioteca")
                if not name: raise ValueError("El nombre del proyecto no puede estar vacío")
                yaml = selected / "project.yaml"; raw = yaml.read_text(encoding="utf-8", errors="replace")
                raw = re.sub(r"(?m)^name:.*$", f"name: {name!r}", raw, count=1)
                yaml.write_text(raw, encoding="utf-8"); rename_project(LIBRARY_DB, selected, name)
                return self.json({"ok": True, "name": name})
            except Exception as error: return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/delete-project":
            try:
                size = int(self.headers.get("Content-Length", "0")); data = json.loads(self.rfile.read(size))
                selected = Path(str(data.get("path", ""))).resolve(); library_projects_root = (LIBRARY_ROOT / "projects").resolve()
                if library_projects_root not in selected.parents or not (selected / "project.yaml").is_file(): raise ValueError("Proyecto no válido en la biblioteca")
                if selected == ROOT.resolve(): raise ValueError("Cierra el proyecto activo antes de eliminarlo")
                shutil.rmtree(selected); remove_project(LIBRARY_DB, selected)
                return self.json({"ok": True, "message": "Proyecto eliminado de la biblioteca."})
            except Exception as error: return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/save-project-setup":
            try:
                size = int(self.headers.get("Content-Length", "0")); data = json.loads(self.rfile.read(size))
                save_project(ROOT, data.get("metadata"), data.get("structure"))
                return self.json({"ok": True, "message": "Configuración del proyecto guardada."})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/add-project-pdfs":
            try:
                fields, files = self.multipart_fields()
                pdf_files = [(name, content) for name, content in files if Path(name).suffix.lower() == ".pdf"]
                if not pdf_files: raise ValueError("Selecciona uno o más archivos PDF")
                destination = ROOT / "fuentes" / "pdf"; destination.mkdir(parents=True, exist_ok=True)
                project = load_project(ROOT); inventory = project.get("inventory", {}); documents = inventory.setdefault("documents", [])
                units = project.get("structure", {}).setdefault("units", []); added = []
                for original_name, content in pdf_files:
                    safe_name = Path(original_name).name
                    target = destination / safe_name
                    if target.exists():
                        digest = hashlib.sha256(content).hexdigest()[:10]
                        target = destination / f"{Path(safe_name).stem}-{digest}{Path(safe_name).suffix.lower()}"
                    target.write_bytes(content)
                    reader = PdfReader(str(target)); pages = []
                    for number, page in enumerate(reader.pages, 1):
                        text = (page.extract_text() or "").strip()
                        pages.append({"page": number, "text": text, "text_length": len(text)})
                    relative = str(target.relative_to(destination)).replace("\\", "/")
                    documents.append({"file": relative, "sha256": hashlib.sha256(content).hexdigest(), "pages": pages})
                    stem = Path(relative).stem
                    from create_pdf_project import classify
                    unit = {"id": stem, "name": stem, "section": classify(relative), "file": relative, "pages": [1, len(pages)]}
                    if any(existing.get("id") == unit["id"] for existing in units): unit["id"] = f"{stem}-{len(units)+1}"
                    units.append(unit); added.append(unit)
                inventory["documents"] = documents; inventory["status"] = "intake_complete"; inventory["next"] = "classify_and_generate_auditable_dtbook_proposal"
                (ROOT / "inventario" / "project.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                save_project(ROOT, structure={"units": units})
                return self.json({"ok": True, "message": f"{len(added)} PDF agregado(s) al proyecto.", "units": added})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/create-editorial-pdf":
            try:
                output = ROOT / "fuentes" / "pdf" / "generated-frontmatter.pdf"
                process = subprocess.run([sys.executable, "nimas-agent/create_editorial_pdf.py", "--project", str(ROOT), "--output", str(output)], cwd=APP_ROOT, text=True, capture_output=True)
                if process.returncode: return self.json({"error": process.stderr.strip() or process.stdout.strip()}, 400)
                project=load_project(ROOT); units=project.get("structure",{}).get("units",[])
                if not any(unit.get("id")=="generated-frontmatter" for unit in units):
                    units.append({"id":"generated-frontmatter","name":"Generated frontmatter","section":"frontmatter","file":output.name,"pages":[1,3]})
                    save_project(ROOT, structure={"units":units})
                return self.json({"ok": True, "message": "PDF editorial generado; requiere revisión humana.", "path": str(output.relative_to(ROOT)).replace("\\\\","/")})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/assign-image":
            try:
                size=int(self.headers.get("Content-Length","0")); data=json.loads(self.rfile.read(size)); filename=str(data.get("file","")).strip(); unit=str(data.get("unit_id","")).strip(); decision=str(data.get("status","reviewed"))
                if decision!="discarded" and not unit: raise ValueError("Selecciona una unidad antes de marcar la imagen como revisada")
                path=ROOT/"inventario"/"images.json"
                if not path.is_file(): raise ValueError("Primero analiza las imágenes del proyecto")
                report=json.loads(path.read_text(encoding="utf-8")); asset=next((x for x in report.get("assets",[]) if x.get("file")==filename),None)
                if not asset: raise ValueError("Imagen no encontrada en el inventario")
                asset["assigned_unit"]=unit or None; asset["status"]="discarded" if decision=="discarded" else "reviewed"; path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                return self.json({"ok":True,"message":"Decisión de imagen guardada."})
            except Exception as error:
                return self.json({"error":str(error)},400)
        if parsed.path == "/api/prepare-ai-context":
            try:
                size=int(self.headers.get("Content-Length","0")); data=json.loads(self.rfile.read(size)); prompt=write_prompt(ROOT,str(data.get("unit_id","")))
                return self.json({"ok":True,"prompt":prompt,"message":"Contexto de IA preparado como propuesta pendiente."})
            except Exception as error: return self.json({"error":str(error)},400)
        if parsed.path == "/api/generate-ai-proposal":
            try:
                size=int(self.headers.get("Content-Length","0")); data=json.loads(self.rfile.read(size)); unit=str(data.get("unit_id","")).strip()
                if not unit: raise ValueError("Selecciona una unidad")
                with LOCK:
                    if JOBS["running"]: return self.json({"error":"Ya hay una tarea en curso."},409)
                provider=str(data.get("provider", "codex"))
                if provider not in {"codex", "ollama"}: raise ValueError("Proveedor no soportado")
                threading.Thread(target=run_ai_proposal,args=(unit,provider),daemon=True).start()
                return self.json({"ok":True,"message":"Generación de propuesta iniciada."},202)
            except Exception as error: return self.json({"error":str(error)},400)
        if parsed.path == "/api/generate-ai-all":
            try:
                size=int(self.headers.get("Content-Length","0")); data=json.loads(self.rfile.read(size) or b'{}'); provider=str(data.get('provider','codex'))
                units=load_project(ROOT).get('structure',{}).get('units',[])
                if not units: raise ValueError('No hay unidades para generar')
                with LOCK:
                    if JOBS['running']: return self.json({'error':'Ya hay una tarea en curso.'},409)
                threading.Thread(target=run_ai_all,args=(provider,),daemon=True).start(); return self.json({'ok':True,'message':f'Cola iniciada para {len(units)} unidades.'},202)
            except Exception as error: return self.json({'error':str(error)},400)
        if parsed.path == "/api/approve-ai-proposal":
            try:
                size=int(self.headers.get("Content-Length","0")); data=json.loads(self.rfile.read(size)); unit=str(data.get("unit_id","")).strip()
                source=ROOT/"propuestas"/f"{unit}.xml"
                if not source.is_file(): raise ValueError("No existe una propuesta XML para esta unidad.")
                check=subprocess.run([sys.executable, str(APP_ROOT/"nimas-agent"/"validate_ai_proposal.py"), str(source)],cwd=APP_ROOT,text=True,capture_output=True)
                if check.returncode: raise ValueError("La propuesta no supera la validación estructural.")
                target=ROOT/"revision"/"approved"/f"{unit}.xml"; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
                approvals=ROOT/"revision"/"approvals.json"; current=json.loads(approvals.read_text(encoding="utf-8")) if approvals.is_file() else {}; current[unit]=True; approvals.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding="utf-8")
                return self.json({"ok":True,"message":"Propuesta aprobada para exportación."})
            except Exception as error: return self.json({"error":str(error)},400)
        if parsed.path == "/api/unit-page-decision":
            try:
                size=int(self.headers.get("Content-Length", "0")); data=json.loads(self.rfile.read(size)); unit=str(data.get("unit_id", "")).strip(); page=str(int(data.get("page"))); state=str(data.get("status", "pending"))
                if not unit or state not in {"pending", "approved", "correction"}: raise ValueError("Decisión de página inválida")
                path=ROOT / "revision" / "page-decisions.json"; current=json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}; current.setdefault(unit, {})[page]={"status":state,"note":str(data.get("note", "")).strip(),"updated_at":datetime.now().isoformat()}; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(current, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
                return self.json({"ok":True,"message":"Estado de página guardado."})
            except Exception as error: return self.json({"error":str(error)},400)
        if parsed.path == "/api/manual-image-crop":
            try:
                size = int(self.headers.get("Content-Length", "0")); data = json.loads(self.rfile.read(size))
                unit_id = str(data.get("unit_id", "")).strip(); page_number = int(data.get("page")); detail = unit_detail(unit_id, page_number)
                source = ROOT / str(detail.get("pdf") or "")
                if not source.is_file(): raise ValueError("PDF de la unidad no encontrado")
                values = [float(data.get(key)) for key in ("x0", "y0", "x1", "y1")]
                x0, y0, x1, y1 = min(values[0], values[2]), min(values[1], values[3]), max(values[0], values[2]), max(values[1], values[3])
                if x1 - x0 < 0.02 or y1 - y0 < 0.02 or max(x1, y1) > 1.01 or min(x0, y0) < -0.01: raise ValueError("El rectángulo es demasiado pequeño o está fuera de la página")
                import fitz
                try: printed_first = int(detail["pages"][0])
                except (TypeError, ValueError): printed_first = 1
                with fitz.open(str(source)) as document:
                    index = page_number - printed_first
                    if index < 0 or index >= len(document): raise ValueError("Página fuera del rango del PDF")
                    pdf_page = document[index]; rect = pdf_page.rect
                    clip = fitz.Rect(rect.x0 + x0 * rect.width, rect.y0 + y0 * rect.height, rect.x0 + x1 * rect.width, rect.y0 + y1 * rect.height)
                    pixmap = pdf_page.get_pixmap(matrix=fitz.Matrix(4.1667, 4.1667), clip=clip, alpha=False)
                    output = ROOT / "working" / "detected-images"; output.mkdir(parents=True, exist_ok=True)
                    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", unit_id); filename = f"{safe}_p{page_number:04d}_manual_{datetime.now():%H%M%S%f}.png"; target = output / filename; pixmap.save(str(target))
                inventory_path = ROOT / "inventario" / "images.json"; inventory = json.loads(inventory_path.read_text(encoding="utf-8")) if inventory_path.is_file() else {"schema":"nimas-assets/1","assets":[]}
                inventory.setdefault("assets", []).append({"file": filename, "source_pdf": Path(str(detail["unit"].get("file", ""))).name, "page": page_number, "display_page": page_number, "status":"reviewed", "assigned_unit":unit_id, "candidate_units":[unit_id], "manual":True, "rect":[x0,y0,x1,y1], "referenced":False})
                inventory["count"] = len([asset for asset in inventory["assets"] if asset.get("status") != "discarded"]); inventory_path.parent.mkdir(parents=True, exist_ok=True); inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
                return self.json({"ok":True,"message":"Imagen manual extraída y asociada a la página.","asset":{"file":filename,"page":page_number,"url":"/working/detected-images/"+filename}})
            except Exception as error: return self.json({"error":str(error)},400)
        if parsed.path == "/api/approve-unit":
            try:
                size=int(self.headers.get("Content-Length", "0")); data=json.loads(self.rfile.read(size)); unit_id=str(data.get("unit_id", "")).strip(); unit=project_unit(unit_id)
                if not unit: raise ValueError("Unidad no encontrada")
                detail=unit_detail(unit_id); first,last=map(int,detail["pages"]); decisions=detail.get("decisions", {}); missing=[str(page) for page in range(first,last+1) if decisions.get(str(page),{}).get("status")!="approved"]
                if missing: raise ValueError("Faltan páginas por aprobar: "+", ".join(missing[:12]))
                source=ROOT/"propuestas"/f"{unit_id}.xml"; check=subprocess.run([sys.executable,str(APP_ROOT/"nimas-agent"/"validate_ai_proposal.py"),str(source)],cwd=APP_ROOT,text=True,capture_output=True)
                if check.returncode: raise ValueError("La propuesta no supera la validación estructural.")
                target=ROOT/"revision"/"approved"/f"{unit_id}.xml"; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target); approvals=ROOT/"revision"/"approvals.json"; current=json.loads(approvals.read_text(encoding="utf-8")) if approvals.is_file() else {}; current[unit_id]=True; approvals.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding="utf-8")
                return self.json({"ok":True,"message":"Unidad aprobada para exportación."})
            except Exception as error: return self.json({"error":str(error)},400)
        if parsed.path == "/api/analyze-project-assets":
            try:
                with LOCK:
                    if JOBS["running"]: return self.json({"error":"Ya hay una tarea en curso."},409)
                threading.Thread(target=run_assets, daemon=True).start()
                return self.json({"ok":True,"message":"Análisis de imágenes iniciado."},202)
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/approve-lesson":
            try:
                number = int(query.get("lesson", [""])[0])
                entry = next(item for item in lessons() if item["lesson"] == number)
                if not entry["hasProposal"]:
                    raise ValueError("No existe propuesta para esta lección")
                check = subprocess.run([sys.executable, "nimas-agent/validar_propuesta_leccion.py", str(number)], cwd=ROOT, text=True, capture_output=True)
                if check.returncode:
                    raise ValueError(check.stderr.strip() or check.stdout.strip())
                record = ROOT / "nimas-review" / "registro-aprobaciones.md"
                text = record.read_text(encoding="utf-8")
                if not re.search(rf"\| L{number:02d} \|[^|]*\| Aprobada", text):
                    line = f"| L{number:02d} | {entry['first']}–{entry['last']} | Aprobada | Aprobada página por página desde el gestor; propuesta validada. |\n"
                    record.write_text(text.rstrip() + "\n" + line, encoding="utf-8")
                return self.json({"ok": True, "message": f"L{number:02d} quedó aprobada y registrada."})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/accept-editorial-proposal":
            try:
                key = query.get("section", [""])[0].upper()
                if key not in {"FM", "EM"}:
                    raise ValueError("Sección editorial inválida")
                validate_editorial_proposal(key)
                entry = next(section for section in editorial_sections() if section["key"] == key)
                record = ROOT / "nimas-review" / "registro-aprobaciones.md"
                text = record.read_text(encoding="utf-8")
                if not re.search(rf"\| {key} \|[^|]*\| Aprobada", text):
                    line = f"| {key} | {entry['pages']} | Aprobada | Propuesta editorial revisada y aceptada desde el gestor; no modifica todavía el paquete NIMAS. |\n"
                    record.write_text(text.rstrip() + "\n" + line, encoding="utf-8")
                return self.json({"ok": True, "message": f"La propuesta de {key} quedó aceptada y registrada."})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/request-adjustment":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(size))
                unit_id = str(data.get("unit_id", "")).strip()
                page = int(data.get("page"))
                note = str(data.get("note", "")).strip()
                if not note:
                    raise ValueError("Escribe la solicitud editorial antes de guardarla")
                if unit_id:
                    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", unit_id)
                    target = ROOT / "revision" / "adjustments" / f"{safe}-p{page:04d}.md"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(f"# Solicitud editorial · {unit_id}, página {page}\n\n{note}\n", encoding="utf-8")
                else:
                    number = int(data.get("lesson"))
                    adjustment_path(number, page).write_text(f"# Solicitud editorial · L{number:02d}, página {page}\n\n{note}\n", encoding="utf-8")
                if unit_id:
                    # Generic PDF units are intentionally queued as a durable
                    # human request. The legacy page-adjustment worker only
                    # understands numbered lessons and must not be invoked.
                    return self.json({"ok": True, "queued": False,
                                      "message": f"Solicitud guardada para la unidad {unit_id}, página {page}."})
                with LOCK:
                    if JOBS["running"]:
                        return self.json({"error": "Hay una generación en curso. La solicitud quedó guardada; envíala cuando termine para corregir solo esta página."}, 409)
                    JOBS["events"] = [event for event in JOBS["events"] if event.get("lesson") != number]
                threading.Thread(target=run_page_adjustment, args=(number, page), daemon=True).start()
                return self.json({"ok": True, "queued": True, "message": f"Solicitud enviada. El agente corregirá solo la página {page}."})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/create-project":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(size))
                if isinstance(data.get("pdf"), str) and data.get("pdf").strip() and not data.get("original"):
                    name = str(data.get("name") or Path(data["pdf"]).stem).strip()
                    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "proyecto"
                    project_path = LIBRARY_ROOT / "projects" / safe
                    command = [sys.executable, "nimas-agent/create_pdf_project.py", "--pdf", data["pdf"], "--destino", str(project_path), "--nombre", name]
                    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
                    if process.returncode:
                        return self.json({"error": process.stderr.strip() or process.stdout.strip()}, 400)
                    register(LIBRARY_DB, name, project_path)
                    return self.json({"ok": True, "project": {"name": name, "path": str(project_path)}, "message": process.stdout.strip()})
                required = ["original", "progreso", "pdf", "destino"]
                if any(not isinstance(data.get(key), str) or not data[key].strip() for key in required):
                    raise ValueError("Completa las cuatro rutas de carpetas")
                command = [sys.executable, "nimas-agent/inicializar_proyecto_nimas.py"]
                for key in required:
                    command.extend([f"--{key}", data[key]])
                process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
                if process.returncode:
                    return self.json({"error": process.stderr.strip() or process.stdout.strip()}, 400)
                return self.json({"ok": True, "message": process.stdout.strip()})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
        if parsed.path == "/api/create-project-upload":
            temp_root = None
            try:
                fields, uploaded = self.multipart_fields()
                name = str(fields.get("name", "")).strip()
                files = [(filename, data) for filename, data in uploaded if str(filename).lower().endswith(".pdf")]
                if not name or not files: raise ValueError("Indica el nombre y selecciona al menos un PDF")
                temp_root = Path(tempfile.mkdtemp(prefix="nimas-upload-"))
                for filename, data in files:
                    target = temp_root / Path(filename).name
                    target.write_bytes(data)
                safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "proyecto"
                project_path = LIBRARY_ROOT / "projects" / safe
                command = [sys.executable, "nimas-agent/create_pdf_project.py", "--pdf", str(temp_root), "--destino", str(project_path), "--nombre", name]
                process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
                if process.returncode: return self.json({"error": process.stderr.strip() or process.stdout.strip()}, 400)
                register(LIBRARY_DB, name, project_path)
                return self.json({"ok": True, "project": {"name": name, "path": str(project_path)}, "message": process.stdout.strip()})
            except Exception as error:
                return self.json({"error": str(error)}, 400)
            finally:
                if temp_root: shutil.rmtree(temp_root, ignore_errors=True)
        if parsed.path == "/api/create-zip-project-upload":
            temp_root = None
            try:
                fields, uploaded = self.multipart_fields(); name=str(fields.get('name','')).strip()
                zips=[(n,d) for n,d in uploaded if str(n).lower().endswith('.zip')]; pdfs=[(n,d) for n,d in uploaded if str(n).lower().endswith('.pdf')]
                if not name or len(zips)!=1: raise ValueError('Indica el nombre y selecciona un ZIP NIMAS')
                temp_root=Path(tempfile.mkdtemp(prefix='nimas-zip-upload-')); zip_path=temp_root/Path(zips[0][0]).name; zip_path.write_bytes(zips[0][1]); pdf_paths=[]
                for filename,data_bytes in pdfs: target=temp_root/Path(filename).name; target.write_bytes(data_bytes); pdf_paths.append(str(target))
                safe=re.sub(r'[^A-Za-z0-9_-]+','_',name).strip('_') or 'proyecto'; project_path=LIBRARY_ROOT/'projects'/safe
                command=[sys.executable,'nimas-agent/create_zip_project.py','--zip',str(zip_path),'--destino',str(project_path),'--nombre',name,'--pdf',*pdf_paths]
                process=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
                if process.returncode: return self.json({'error':process.stderr.strip() or process.stdout.strip()},400)
                register(LIBRARY_DB,name,project_path,mode='nimas_zip'); return self.json({'ok':True,'project':{'name':name,'path':str(project_path)},'message':process.stdout.strip()})
            except Exception as error: return self.json({'error':str(error)},400)
            finally:
                if temp_root: shutil.rmtree(temp_root,ignore_errors=True)
        if parsed.path == "/api/generate-editorial":
            key = query.get("section", [""])[0].upper()
            if key not in {"FM", "EM"}: return self.json({"error": "Sección editorial inválida"}, 400)
            with LOCK:
                if JOBS["running"]: return self.json({"error": "Ya hay una generación en curso"}, 409)
            threading.Thread(target=run_editorial_section, args=(key,), daemon=True).start()
            return self.json({"ok": True, "queue": [key], "message": f"Reconstrucción de {key} iniciada desde PDF."}, 202)
        if parsed.path == "/api/export-package":
            with LOCK:
                if JOBS["running"]:
                    return self.json({"error": "Hay una tarea en curso; espera a que termine antes de exportar."}, 409)
            threading.Thread(target=run_export, daemon=True).start()
            return self.json({"ok": True, "queue": ["ZIP"], "message": "Validando y creando el ZIP NIMAS…"}, 202)
        if parsed.path not in {"/api/generate", "/api/generate-pending"}:
            return self.json({"error": "Ruta no disponible"}, 404)
        with LOCK:
            if JOBS["running"]: return self.json({"error": "Ya hay una generación en curso"}, 409)
        if parsed.path == "/api/generate":
            try: numbers = [int(query.get("lesson", [""])[0])]
            except ValueError: return self.json({"error": "Lección inválida"}, 400)
        else:
            numbers = [item["lesson"] for item in lessons() if item["status"] == "pending" and item["lesson"] >= 4]
        if not numbers: return self.json({"ok": True, "message": "No hay propuestas pendientes"})
        threading.Thread(target=run_queue, args=(numbers,), daemon=True).start()
        return self.json({"ok": True, "queue": numbers}, 202)

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Auditor NIMAS: http://127.0.0.1:8000/auditoria-lecciones/")
    server.serve_forever()
