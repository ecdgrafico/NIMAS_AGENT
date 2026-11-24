#!/usr/bin/env python3
"""Generate a review-only DTBook proposal with an available AI provider."""
import argparse, html, json, re, shutil, subprocess, sys
from pathlib import Path
from ai_provider import provider_status, write_prompt
from ai_provider import find_ollama

def extract_xml_candidate(raw: str) -> str | None:
    """Keep only a complete XML fragment; never store model prose as DTBook."""
    text = raw.strip()
    match = re.search(r"<level1\b[\s\S]*?</level1>", text)
    return match.group(0).strip() + "\n" if match else None

def pdf_completeness_errors(root: Path, unit_id: str, xml_path: Path) -> list[str]:
    """Reject a well-formed but obviously incomplete PDF reconstruction."""
    structure_path = root / "structure" / "structure.json"
    inventory_path = root / "inventario" / "project.json"
    if not structure_path.is_file() or not inventory_path.is_file(): return []
    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    unit = next((item for item in structure.get("units", []) if item.get("id") == unit_id), None)
    if not unit: return []
    expected = max(0, int((unit.get("pages") or [1, 1])[1]) - int((unit.get("pages") or [1, 1])[0]) + 1)
    if expected < 3: return []
    text = xml_path.read_text(encoding="utf-8", errors="replace")
    errors = []
    if "Texto visible." in text or "Título</h1><p>Texto visible." in text:
        errors.append("La propuesta contiene el texto de ejemplo del prompt y no una reconstrucción del PDF.")
    anchors = {int(value) for value in re.findall(r"<pagenum\b[^>]*>\s*(\d+)\s*</pagenum>", text, re.I)}
    minimum = max(2, int(expected * 0.8))
    if len(anchors) < minimum:
        errors.append(f"La propuesta contiene {len(anchors)} anclas de página; se requieren al menos {minimum} para {expected} páginas PDF.")
    return errors

def combine_level1_fragments(fragments: list[str]) -> str:
    """Combine independently generated level1 fragments without adding a package wrapper."""
    from lxml import etree
    roots = [etree.fromstring(fragment.encode("utf-8")) for fragment in fragments]
    master = roots[0]
    for root in roots[1:]:
        for child in list(root):
            if child.tag == "h1":
                continue
            master.append(child)
    return etree.tostring(master, encoding="unicode", pretty_print=True)

def baseline_fragment(root: Path, unit: dict, start: int, end: int) -> str:
    """Create a faithful text/page baseline when a local model misses a block."""
    inventory = json.loads((root / "inventario" / "project.json").read_text(encoding="utf-8"))
    filename = Path(str(unit.get("file", ""))).name
    document = next((item for item in inventory.get("documents", []) if Path(str(item.get("file", ""))).name == filename), {})
    pages = {int(item.get("page", 0)): item.get("text", "") for item in document.get("pages", [])}
    parts = ["<level1>", f"<h1>{html.escape(str(unit.get('name', unit.get('id', 'Unidad'))))}</h1>"]
    for page in range(start, end + 1):
        text = str(pages.get(page, "")).strip()
        parts.append(f'<pagenum page="normal">{page}</pagenum>')
        if text:
            for paragraph in re.split(r"\n\s*\n", text):
                value = " ".join(paragraph.split())
                if value: parts.append(f"<p>{html.escape(value)}</p>")
        else:
            parts.append("<p>Contenido de página pendiente de revisión visual.</p>")
    parts.append("</level1>")
    return "\n".join(parts)

def ollama_generate(executable, model: str, root: Path, instruction: str, expected_pages: int, unit_id: str) -> str:
    """Generate in page blocks so a local model cannot truncate a whole lesson."""
    if expected_pages <= 8:
        result = subprocess.run([str(executable), "run", model], cwd=root, input=instruction, text=True, encoding="utf-8", capture_output=True)
        if result.returncode: raise SystemExit(result.stderr.strip() or "Ollama no generó la propuesta.")
        return result.stdout
    fragments = []
    structure = json.loads((root/'structure'/'structure.json').read_text(encoding='utf-8'))
    unit = next((item for item in structure.get('units', []) if item.get('id') == unit_id), {})
    # The caller's unit is injected in the prompt; the fallback uses the same
    # source inventory and is selected below only when the model misses a block.
    for start in range(1, expected_pages + 1, 5):
        end = min(expected_pages, start + 4)
        chunk_instruction = instruction + f"\n\nBLOQUE ACTUAL: trabaja únicamente las páginas PDF {start} a {end}. Entrega un level1 con esas páginas y no omitas ninguna."
        result = subprocess.run([str(executable), "run", model], cwd=root, input=chunk_instruction, text=True, encoding="utf-8", capture_output=True)
        if result.returncode: raise SystemExit(result.stderr.strip() or f"Ollama falló en páginas {start}-{end}.")
        candidate = extract_xml_candidate(result.stdout)
        if not candidate or len({int(value) for value in re.findall(r"<pagenum\b[^>]*>\s*(\d+)\s*</pagenum>", candidate, re.I)}) < (end - start + 1) * 0.8:
            candidate = baseline_fragment(root, unit, start, end)
        fragments.append(candidate)
    return combine_level1_fragments(fragments)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project',type=Path,required=True); ap.add_argument('--unit',required=True); ap.add_argument('--provider',default='codex'); args=ap.parse_args()
    root=args.project.resolve(); prompt=Path(write_prompt(root,args.unit)); output=root/'propuestas'/f'{args.unit}.xml'; runlog=root/'versions'/'ai-runs'; runlog.mkdir(parents=True,exist_ok=True)
    instruction=prompt.read_text(encoding='utf-8')+f'''\n\nEscribe únicamente un fragmento XML DTBook bien formado en {output}. No modifiques fuentes. Si no puedes verificar una parte, conserva la incertidumbre en {runlog/(args.unit+'-dudas.md')}. La salida queda pendiente de auditoría humana.'''
    structure = json.loads((root/'structure'/'structure.json').read_text(encoding='utf-8'))
    unit = next((item for item in structure.get('units', []) if item.get('id') == args.unit), {})
    first, last = (unit.get('pages') or [1, 1])
    expected_pages = max(1, int(last) - int(first) + 1)
    instruction += "\n\nREGLA DE SALIDA: entrega solo un fragmento XML completo cuya raíz sea level1. No incluyas dtbook, book, frontmatter, bodymatter, rearmatter, package, Markdown ni explicaciones fuera del XML."
    printed_range=unit.get('source_page_range') or 'por deducir del PDF'
    instruction += f"\n\nCOBERTURA OBLIGATORIA: la unidad tiene {expected_pages} páginas físicas PDF. El rango impreso sugerido por el nombre es {printed_range}; debes leer el PDF y deducir los valores reales de pagenum. Conserva páginas impresas que comiencen en 0, como LP 000, y numeración romana de frontmatter cuando aparezca. Emite una etiqueta <pagenum> por cada página física y transcribe/estructura su contenido visible. No entregues un resumen ni un ejemplo abreviado. Si una página no tiene texto, conserva su <pagenum> y marca la incertidumbre para revisión humana."
    if args.provider=='codex':
        executable=shutil.which('codex')
        if not executable: raise SystemExit('Codex CLI no está disponible en PATH.')
        instruction_path=runlog/(args.unit+'-instruction.md'); instruction_path.write_text(instruction,encoding='utf-8')
        short_instruction=f'Read and follow the complete instructions in {instruction_path}. Create the requested XML proposal and do not modify source files.'
        result=subprocess.run([executable,'exec','--sandbox','workspace-write','--add-dir',str(root),'--skip-git-repo-check','--ephemeral','-C',str(root),'-o',str(runlog/(args.unit+'-codex.md')),short_instruction],cwd=root,text=True,capture_output=True)
    elif args.provider=='ollama':
        executable=find_ollama()
        if not executable: raise SystemExit('Ollama no está disponible en PATH.')
        model = __import__('os').environ.get('NIMAS_OLLAMA_MODEL','llama3.2')
        # Send the prompt through stdin so long PDF/XML evidence never hits
        # Windows' command-line length limit.
        result = type('Result', (), {'returncode': 0, 'stdout': ollama_generate(executable, model, root, instruction, expected_pages, args.unit), 'stderr': ''})()
        (runlog/(args.unit+'-ollama.md')).write_text(result.stdout,encoding='utf-8')
        if 'Contenido de página pendiente de revisión visual.' in result.stdout:
            (runlog/(args.unit+'-fallback.md')).write_text(
                'Algunos bloques no produjeron XML suficiente con Ollama. '
                'Se incorporó una transcripción literal del texto extraído del PDF; '
                'requiere revisión semántica y visual humana.\n', encoding='utf-8')
        if result.returncode==0:
            candidate=extract_xml_candidate(result.stdout)
            if candidate:
                if output.is_file():
                    previous=runlog/(args.unit+'-previous.xml')
                    previous.write_text(output.read_text(encoding='utf-8'),encoding='utf-8')
                output.write_text(candidate,encoding='utf-8')
            else: raise SystemExit(f'Ollama no produjo un fragmento level1 completo. Revisa {runlog/(args.unit+"-ollama.md")}')
    else:
        raise SystemExit('Proveedor no soportado: '+args.provider)
    if result.returncode: raise SystemExit(result.stderr.strip() or result.stdout.strip() or 'Codex no generó la propuesta.')
    if not output.is_file():
        diagnostic=(runlog/(args.unit+'-codex.md')).read_text(encoding='utf-8',errors='replace')[-1000:] if (runlog/(args.unit+'-codex.md')).is_file() else ''
        raise SystemExit(f'Codex terminó sin crear {output}. Diagnóstico: {diagnostic}')
    report = runlog / f'{args.unit}-validation.json'
    coverage_errors = pdf_completeness_errors(root, args.unit, output)
    if coverage_errors:
        report.write_text(json.dumps({'status':'fail','path':str(output),'errors':coverage_errors}, ensure_ascii=False, indent=2), encoding='utf-8')
        output.unlink(missing_ok=True)
        raise SystemExit(f'La propuesta quedó incompleta respecto al PDF. Revisa {report}')
    check = subprocess.run([sys.executable, str(Path(__file__).with_name('validate_ai_proposal.py')), str(output), '--report', str(report)], cwd=root, text=True, capture_output=True)
    if check.returncode: raise SystemExit(f'La propuesta quedó pendiente por errores de estructura. Revisa {report}')
    print(f'Propuesta pendiente creada: {output}')

if __name__=='__main__': main()
