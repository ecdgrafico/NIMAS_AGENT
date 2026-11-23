#!/usr/bin/env python3
"""Local project server for the NIMAS audit dashboard.

It exposes project discovery, on-demand PDF rendering, and an explicit queue
for proposal generation. It never installs a proposal into the NIMAS package.
"""
import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
import shutil
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from lxml import etree

ROOT = Path(os.environ.get("NIMAS_PROJECT_ROOT", Path(__file__).resolve().parent.parent)).resolve()
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
    required = ["lecciones_originales", "PDF", "9781669952961NIMAS", "9781669952961NIMAS_original"]
    ready = all((ROOT / path).exists() for path in required)
    return {"ready": ready, "name": ROOT.name if ready else None}

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
        process = subprocess.run([sys.executable, "nimas-agent/exportar_paquete_nimas.py"], cwd=ROOT, text=True, capture_output=True)
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

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        relative = Path(urlparse(path).path.lstrip("/"))
        target = (ROOT / relative).resolve()
        return str(target if ROOT in target.parents or target == ROOT else ROOT)
    def json(self, value, status=200):
        payload = json.dumps(value).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/project-status": return self.json(project_status())
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
        if parsed.path == "/":
            self.send_response(HTTPStatus.SEE_OTHER); self.send_header("Location", "/auditoria-lecciones/"); self.end_headers(); return
        return super().do_GET()
    def do_POST(self):
        parsed = urlparse(self.path); query = parse_qs(parsed.query)
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
                number, page = int(data.get("lesson")), int(data.get("page"))
                note = str(data.get("note", "")).strip()
                if not note:
                    raise ValueError("Escribe la solicitud editorial antes de guardarla")
                adjustment_path(number, page).write_text(
                    f"# Solicitud editorial · L{number:02d}, página {page}\n\n{note}\n", encoding="utf-8")
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
