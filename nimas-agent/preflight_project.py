#!/usr/bin/env python3
"""Report actionable readiness checks for a NIMAS project."""
import argparse, json
from pathlib import Path

def preflight(root: Path):
    metadata=json.loads((root/'metadata/nimac.json').read_text(encoding='utf-8')) if (root/'metadata/nimac.json').is_file() else {}
    structure=json.loads((root/'structure/structure.json').read_text(encoding='utf-8')) if (root/'structure/structure.json').is_file() else {'units':[]}
    images=json.loads((root/'inventario/images.json').read_text(encoding='utf-8')) if (root/'inventario/images.json').is_file() else {'assets':[]}
    checks=[]; required=('title','identifier','language')
    for key in required: checks.append({'id':'metadata_'+key,'ok':bool(str(metadata.get(key,'')).strip()),'message':f'Metadata {key}'})
    units=structure.get('units',[]); checks.append({'id':'units','ok':bool(units),'message':f'{len(units)} unidades'}); checks.append({'id':'classified','ok':all(u.get('section')!='unclassified' for u in units),'message':'Unidades clasificadas'})
    pending=[a.get('file') for a in images.get('assets',[]) if a.get('status')=='detected']
    checks.append({'id':'images','ok':not pending,'message':f'{len(pending)} imágenes pendientes de decisión'})
    return {'status':'pass' if all(x['ok'] for x in checks) else 'pending','checks':checks}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project',type=Path,required=True); ap.add_argument('--report',type=Path); args=ap.parse_args(); result=preflight(args.project.resolve()); print(json.dumps(result,ensure_ascii=False));
    if args.report: args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit(0 if result['status']=='pass' else 1)

if __name__=='__main__': main()
