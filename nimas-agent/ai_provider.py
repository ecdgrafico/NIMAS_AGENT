"""Provider-neutral proposal preparation for Codex, Ollama or manual review."""
import json
import os
import shutil
import subprocess
from pathlib import Path

def find_ollama():
    return shutil.which('ollama') or next((p for p in (Path(os.environ.get('LOCALAPPDATA',''))/'Programs'/'Ollama'/'ollama.exe', Path(os.environ.get('ProgramFiles',''))/'Ollama'/'ollama.exe') if p.is_file()), None)

def ollama_models(executable):
    if not executable: return []
    try:
        result=subprocess.run([str(executable),'list'],capture_output=True,text=True,encoding='utf-8',timeout=4)
        if result.returncode: return []
        return [line.split()[0] for line in result.stdout.splitlines()[1:] if line.split()]
    except (OSError, subprocess.SubprocessError):
        return []

def provider_status():
    ollama=find_ollama()
    codex=shutil.which('codex')
    models=ollama_models(ollama)
    return {'providers':[{'id':'manual','label':'Revision manual','available':True},{'id':'ollama','label':'Ollama local','available':bool(models),'executable':str(ollama) if ollama else None,'models':models},{'id':'codex','label':'Codex CLI','available':bool(codex),'executable':codex}]}

def build_context(root: Path):
    inventory=root/'inventario'/'project.json'; structure=root/'structure'/'structure.json'; metadata=root/'metadata'/'nimac.json'; images=root/'inventario'/'images.json'
    return {'metadata':json.loads(metadata.read_text(encoding='utf-8')) if metadata.is_file() else {},'structure':json.loads(structure.read_text(encoding='utf-8')) if structure.is_file() else {'units':[]},'inventory':json.loads(inventory.read_text(encoding='utf-8')) if inventory.is_file() else {},'images':json.loads(images.read_text(encoding='utf-8')) if images.is_file() else {'assets':[]}}

def write_prompt(root: Path, unit_id: str):
    context=build_context(root); unit=next((x for x in context['structure'].get('units',[]) if x.get('id')==unit_id),None)
    if not unit: raise ValueError(f'Unidad no encontrada: {unit_id}')
    source = root/'fuentes'/'pdf'/str(unit.get('file',''))
    source_info = {'path': str(source), 'exists': source.is_file()}
    if context['inventory'].get('source_mode') == 'nimas_zip':
        original = root / str(context['inventory'].get('xml_source') or '')
        if original.is_file():
            source_info['original_xml_path'] = str(original)
            source_info['original_xml_excerpt'] = original.read_text(encoding='utf-8', errors='replace')[:120000]
        opf = root / str(context['inventory'].get('opf_source') or '')
        if opf.is_file(): source_info['original_opf_path'] = str(opf)
    for document in context['inventory'].get('documents',[]):
        if document.get('file') == Path(str(unit.get('file',''))).name:
            first,last=(unit.get('pages') or [1,len(document.get('pages',[]))]); source_info['pages']=document.get('pages',[])[max(0,int(first)-1):int(last)]
            break
    source_info['image_assets']=[asset for asset in context['images'].get('assets',[]) if unit_id in (asset.get('candidate_units') or []) or asset.get('source_pdf')==Path(str(unit.get('file',''))).name]
    references=[]
    for reference in context['structure'].get('units',[]):
        if not reference.get('reference') or reference.get('id') == unit_id: continue
        candidates=[root/'revision'/'approved'/f"{reference.get('id')}.xml", root/'propuestas'/f"{reference.get('id')}.xml"]
        example=next((path for path in candidates if path.is_file()), None)
        if example:
            references.append({'unit_id':reference.get('id'),'name':reference.get('name'),'xml_excerpt':example.read_text(encoding='utf-8',errors='replace')[:60000]})
    prompt=(root/'propuestas'/f'{unit_id}.prompt.md')
    prompt.parent.mkdir(parents=True,exist_ok=True)
    prompt.write_text(f'''# Propuesta DTBook · {unit_id}\n\n## Instrucciones\nConstruye una propuesta DTBook NIMAS completa para esta unidad. El PDF indicado y el texto extraído por página son la autoridad editorial. No inventes contenido. Conserva pagenum, jerarquía semántica, listas, tablas, captions e imágenes. Entrega solo XML DTBook bien formado y deja cualquier incertidumbre como pendiente de revisión.\n\n## Unidad\n{json.dumps(unit,ensure_ascii=False,indent=2)}\n\n## Evidencia PDF\n{json.dumps(source_info,ensure_ascii=False,indent=2)}\n\n## Metadata\n{json.dumps(context['metadata'],ensure_ascii=False,indent=2)}\n\n## Lecciones de referencia\nUsa estas unidades solo como evidencia de estructura y semántica. No copies su contenido ni supongas que sus reglas aplican si el PDF actual contradice el patrón.\n{json.dumps(references,ensure_ascii=False,indent=2)}\n''',encoding='utf-8')
    return str(prompt)
