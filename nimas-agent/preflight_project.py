#!/usr/bin/env python3
"""Report actionable readiness checks for a NIMAS project."""
import argparse, json
from pathlib import Path
from lxml import etree

def preflight(root: Path):
    metadata=json.loads((root/'metadata/nimac.json').read_text(encoding='utf-8')) if (root/'metadata/nimac.json').is_file() else {}
    structure=json.loads((root/'structure/structure.json').read_text(encoding='utf-8')) if (root/'structure/structure.json').is_file() else {'units':[]}
    images=json.loads((root/'inventario/images.json').read_text(encoding='utf-8')) if (root/'inventario/images.json').is_file() else {'assets':[]}
    checks=[]; required=('title','publisher','identifier','language','source_isbns','subjects','publication_year','copyright_year','state_edition','content_type')
    for key in required:
        value=metadata.get(key,'')
        ok=bool(value) if isinstance(value,list) else bool(str(value).strip())
        checks.append({'id':'metadata_'+key,'ok':ok,'message':f'Metadata {key}'})
    subjects=metadata.get('subjects') or []; subjects=subjects if isinstance(subjects,list) else [subjects]
    grades=metadata.get('grade_levels') or []; grades=grades if isinstance(grades,list) else [grades]
    checks.append({'id':'subject_limit','ok':len(subjects)<=3,'message':f'{len(subjects)}/3 materias NIMAC'})
    checks.append({'id':'grade_limit','ok':len(grades)<=7,'message':f'{len(grades)}/7 niveles de grado'})
    units=structure.get('units',[]); checks.append({'id':'units','ok':bool(units),'message':f'{len(units)} unidades'}); checks.append({'id':'classified','ok':all(u.get('section')!='unclassified' for u in units),'message':'Unidades clasificadas'})
    approvals=json.loads((root/'revision/approvals.json').read_text(encoding='utf-8')) if (root/'revision/approvals.json').is_file() else {}
    approved_count=sum(1 for u in units if approvals.get(u.get('id')) is True)
    checks.append({'id':'approvals','ok':bool(units) and approved_count==len(units),'message':f'{approved_count}/{len(units)} unidades aprobadas humanamente'})
    invalid=[]
    for unit in units:
        path=root/'revision'/'approved'/f"{unit.get('id')}.xml"
        if approvals.get(unit.get('id')) is True:
            try: etree.parse(str(path))
            except (OSError, etree.XMLSyntaxError): invalid.append(unit.get('id'))
    checks.append({'id':'approved_xml','ok':not invalid and approved_count==len(units),'message':'XML aprobados disponibles y bien formados' if not invalid else 'XML aprobado ausente o inválido: '+', '.join(invalid)})
    pending=[a.get('file') for a in images.get('assets',[]) if a.get('status')=='detected' or (a.get('status')=='reviewed' and not a.get('assigned_unit'))]
    checks.append({'id':'images','ok':not pending,'message':f'{len(pending)} imágenes pendientes de decisión'})
    return {'status':'pass' if all(x['ok'] for x in checks) else 'pending','checks':checks}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project',type=Path,required=True); ap.add_argument('--report',type=Path); args=ap.parse_args(); result=preflight(args.project.resolve()); print(json.dumps(result,ensure_ascii=False));
    if args.report: args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit(0 if result['status']=='pass' else 1)

if __name__=='__main__': main()
