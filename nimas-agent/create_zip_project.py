#!/usr/bin/env python3
"""Create a non-destructive library project from an existing NIMAS ZIP."""
import argparse, json, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path
from lxml import etree

def safe_extract(archive, target):
    target = target.resolve()
    for info in archive.infolist():
        destination = (target / info.filename).resolve()
        if target not in destination.parents and destination != target: raise ValueError("ZIP contiene una ruta insegura")
        archive.extract(info, target)

def audit_package(root, xmls, opfs):
    findings=[]
    for path in xmls:
        try: etree.parse(str(path))
        except Exception as exc: findings.append({'severity':'error','file':str(path.relative_to(root)),'message':f'XML no bien formado: {exc}'})
    for path in opfs:
        try:
            tree=etree.parse(str(path)); base=path.parent
            for item in tree.xpath('//*[local-name()="manifest"]/*[local-name()="item"]'):
                href=item.get('href')
                if href and not (base/href).is_file(): findings.append({'severity':'error','file':str(path.relative_to(root)),'message':f'Recurso OPF inexistente: {href}'})
        except Exception as exc: findings.append({'severity':'error','file':str(path.relative_to(root)),'message':f'OPF no bien formado: {exc}'})
    return {'status':'pass' if not findings else 'fail','xml_count':len(xmls),'opf_count':len(opfs),'findings':findings}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--zip',type=Path,required=True); ap.add_argument('--destino',type=Path,required=True); ap.add_argument('--nombre',required=True); ap.add_argument('--pdf',type=Path,nargs='*',default=[]); args=ap.parse_args()
    if not args.zip.is_file(): raise SystemExit('No existe el ZIP')
    root=args.destino.resolve(); root.mkdir(parents=True,exist_ok=True)
    for folder in ('fuentes/nimas-original','fuentes/pdf','metadata','structure','inventario','working','propuestas','revision','versions','deliverables'): (root/folder).mkdir(parents=True,exist_ok=True)
    shutil.copy2(args.zip, root/'fuentes/nimas-original'/args.zip.name)
    with zipfile.ZipFile(args.zip) as archive: safe_extract(archive, root/'fuentes/nimas-original')
    for pdf in args.pdf:
        if pdf.is_file(): shutil.copy2(pdf, root/'fuentes/pdf'/pdf.name)
    is_system=lambda p: '__MACOSX' in p.parts or p.name.startswith('._') or p.name in {'.DS_Store','Thumbs.db'}
    xmls=[p for p in (root/'fuentes/nimas-original').rglob('*.xml') if not is_system(p)]; opfs=[p for p in (root/'fuentes/nimas-original').rglob('*.opf') if not is_system(p)]
    inventory={'schema':'nimas-project/1','name':args.nombre,'source_mode':'nimas_zip','created_at':datetime.now(timezone.utc).isoformat(),'xml_source':str(xmls[0].relative_to(root)) if xmls else None,'opf_source':str(opfs[0].relative_to(root)) if opfs else None,'reference_pdfs':[p.name for p in (root/'fuentes/pdf').glob('*.pdf')],'status':'intake_complete'}
    (root/'inventario/project.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'metadata/nimac.json').write_text(json.dumps({'title':args.nombre},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    units=[]
    if xmls:
        try:
            tree=etree.parse(str(xmls[0])); body=tree.xpath('//*[local-name()="bodymatter"]')[0]
            candidates=body.xpath('./*[local-name()="level1"]')
            lesson_nodes=[]
            for node in candidates:
                heading=' '.join(''.join(node.xpath('./*[local-name()="h1"][1]//text()')).split())
                if heading.lower().startswith(('lesson ', 'unit ', 'chapter ')): lesson_nodes.append((node,heading))
            if len(lesson_nodes) < 5: lesson_nodes=[(node, ' '.join(''.join(node.xpath('./*[local-name()="h1"][1]//text()')).split())) for node in candidates]
            for index,(node,heading) in enumerate(lesson_nodes,1):
                units.append({'id':f'unit_{index:03d}','name':heading or f'Unidad {index:03d}','section':'bodymatter','source_xml':str(xmls[0].relative_to(root)),'ordinal':index})
        except Exception: units=[]
    (root/'structure/structure.json').write_text(json.dumps({'units':units,'source':'existing_nimas_zip'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'inventario/zip-audit.json').write_text(json.dumps(audit_package(root,xmls,opfs),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'project.yaml').write_text(f"name: {args.nombre!r}\nsource_mode: nimas_zip\nxml_source: {inventory['xml_source']!r}\nopf_source: {inventory['opf_source']!r}\nstatus: intake_complete\n",encoding='utf-8')
    print(f'Proyecto ZIP creado: {root}')

if __name__=='__main__': main()
