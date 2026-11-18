#!/usr/bin/env python3
"""One-command XML-first reconstruction runner for the complete book."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

def run(cmd, cwd):
    print('+', ' '.join(map(str, cmd)), flush=True)
    return subprocess.run(cmd, cwd=str(cwd), check=False).returncode

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--book',required=True); ap.add_argument('--force',action='store_true'); a=ap.parse_args()
    root=a.root.resolve(); py=root/'.venv'/'Scripts'/'python.exe'; work=root/'work'/a.book; orig=work/'9781669952961NIMAS_original'; rec=work/'9781669952961NIMAS_reconstruccion'
    src=root/'work'/a.book/'original'/'9781669952961NIMAS_original'
    if not src.exists(): raise SystemExit(f'No existe la fuente extraída: {src}')
    rec.mkdir(parents=True,exist_ok=True); orig.mkdir(parents=True,exist_ok=True)
    for name in ('9781669952961NIMAS.xml','9781669952961NIMAS.opf','9781669952961NIMAS.pdf'):
        shutil.copy2(src/name,orig/name)
    if (src/'images').exists(): shutil.copytree(src/'images',orig/'images',dirs_exist_ok=True)
    shutil.copy2(orig/'9781669952961NIMAS.xml',rec/'9781669952961NIMAS.xml')
    shutil.copy2(orig/'9781669952961NIMAS.opf',rec/'9781669952961NIMAS.opf')
    if (orig/'9781669952961NIMAS.pdf').exists(): shutil.copy2(orig/'9781669952961NIMAS.pdf',rec/'9781669952961NIMAS.pdf')
    agent=root/'nimas-agent'
    commands=[
      [str(py),str(agent/'rebuild_book_semantics.py')],
      [str(py),str(agent/'clean_invalid_image_refs.py'),str(rec)],
      [str(py),str(agent/'normalize_levels.py'),str(rec/'9781669952961NIMAS.xml')],
      [str(py),str(agent/'normalize_em_anchors.py'),str(rec/'9781669952961NIMAS.xml')],
      [str(py),str(agent/'apply_title_rules.py'),str(rec/'9781669952961NIMAS.xml')],
      [str(py),str(agent/'audit_package.py'),str(rec),'--report',str(work/'preflight-book.json')],
    ]
    for c in commands:
        cwd=work if c[1].endswith('rebuild_book_semantics.py') else root
        if run(c,cwd)!=0 and c[1].endswith('audit_package.py'): return 2
    report={'book':a.book,'status':'xml-audited','package':str(rec),'next':'image matching remains confidence-gated'}
    (work/'book-batch-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0
if __name__=='__main__': sys.exit(main())
