"""Provider-neutral proposal preparation for Codex, Ollama or manual review."""
import json
import os
import shutil
import subprocess
from pathlib import Path

def provider_status():
    ollama=shutil.which('ollama')
    codex=shutil.which('codex')
    return {'providers':[{'id':'manual','label':'Revisión manual','available':True},{'id':'ollama','label':'Ollama local','available':bool(ollama),'executable':ollama},{'id':'codex','label':'Codex CLI','available':bool(codex),'executable':codex}]}

def build_context(root: Path):
    inventory=root/'inventario'/'project.json'; structure=root/'structure'/'structure.json'; metadata=root/'metadata'/'nimac.json'
    return {'metadata':json.loads(metadata.read_text(encoding='utf-8')) if metadata.is_file() else {},'structure':json.loads(structure.read_text(encoding='utf-8')) if structure.is_file() else {'units':[]},'inventory':json.loads(inventory.read_text(encoding='utf-8')) if inventory.is_file() else {}}

def write_prompt(root: Path, unit_id: str):
    context=build_context(root); unit=next((x for x in context['structure'].get('units',[]) if x.get('id')==unit_id),None)
    if not unit: raise ValueError(f'Unidad no encontrada: {unit_id}')
    prompt=(root/'propuestas'/f'{unit_id}.prompt.md')
    prompt.parent.mkdir(parents=True,exist_ok=True)
    prompt.write_text(f'''# Propuesta DTBook · {unit_id}\n\n## Instrucciones\nConstruye una propuesta DTBook NIMAS completa para esta unidad. Usa el PDF como autoridad editorial. No inventes contenido. Conserva pagenum, jerarquía semántica, listas, tablas, captions e imágenes. Entrega solo XML DTBook bien formado y deja cualquier incertidumbre como pendiente de revisión.\n\n## Unidad\n{json.dumps(unit,ensure_ascii=False,indent=2)}\n\n## Metadata\n{json.dumps(context['metadata'],ensure_ascii=False,indent=2)}\n''',encoding='utf-8')
    return str(prompt)
