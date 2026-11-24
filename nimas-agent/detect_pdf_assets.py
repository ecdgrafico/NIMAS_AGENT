#!/usr/bin/env python3
"""Detect and extract PDF image resources into a project working area."""
import argparse
import hashlib
import json
from pathlib import Path
import fitz

def sha256(data): return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project',type=Path,required=True); ap.add_argument('--unit',default=''); args=ap.parse_args()
    root=args.project.resolve(); source=root/'fuentes'/'pdf'; out=root/'working'/'detected-images'; out.mkdir(parents=True,exist_ok=True)
    selected=None
    structure_path=root/'structure'/'structure.json'
    if args.unit and structure_path.is_file():
        units=json.loads(structure_path.read_text(encoding='utf-8')).get('units',[])
        selected=next((u for u in units if u.get('id')==args.unit),None)
    records=[]
    for pdf in sorted(source.rglob('*.pdf')):
        if selected and Path(str(selected.get('file',''))).name != pdf.name: continue
        with fitz.open(str(pdf)) as doc:
            for page_no,page in enumerate(doc,1):
                if selected:
                    pages=selected.get('pages') or [1, len(doc)]
                    if not int(pages[0]) <= page_no <= int(pages[1]): continue
                seen=set()
                for index,img in enumerate(page.get_images(full=True),1):
                    xref=img[0]
                    if xref in seen: continue
                    seen.add(xref)
                    try:
                        extracted=doc.extract_image(xref); data=extracted['image']; ext=extracted.get('ext','png')
                        name=f"{pdf.stem}_p{page_no:04d}_{index:02d}.{ext}"; target=out/name; target.write_bytes(data)
                        rects=[]
                        for rect in page.get_image_rects(xref): rects.append({'x0':rect.x0,'y0':rect.y0,'x1':rect.x1,'y1':rect.y1})
                        records.append({'file':name,'source_pdf':pdf.name,'page':page_no,'xref':xref,'sha256':sha256(data),'width':extracted.get('width'),'height':extracted.get('height'),'ext':ext,'rects':rects,'status':'detected','referenced':False})
                    except Exception as error:
                        records.append({'source_pdf':pdf.name,'page':page_no,'xref':xref,'status':'error','error':str(error)})
    report={'schema':'nimas-assets/1','source':'pdf','count':0,'assets':records}
    existing_path=root/'inventario'/'images.json'
    if args.unit and existing_path.is_file():
        existing=json.loads(existing_path.read_text(encoding='utf-8'))
        new_files={asset.get('file') for asset in records}
        report['assets']=[asset for asset in existing.get('assets',[]) if asset.get('file') not in new_files]+records
    if structure_path.is_file():
        try:
            units=json.loads(structure_path.read_text(encoding='utf-8')).get('units',[])
            for asset in records:
                if asset.get('status')!='detected': continue
                matches=[]
                for unit in units:
                    filename=Path(str(unit.get('file',''))).name
                    pages=unit.get('pages') or [1,0]
                    if filename==asset.get('source_pdf') and int(pages[0])<=int(asset.get('page',0))<=int(pages[1]): matches.append(unit.get('id'))
                asset['candidate_units']=matches
        except Exception:
            pass
    report['count']=len([x for x in report['assets'] if x.get('status')=='detected'])
    (root/'inventario'/'images.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'count':report['count'],'inventory':'inventario/images.json'}))

if __name__=='__main__': main()
