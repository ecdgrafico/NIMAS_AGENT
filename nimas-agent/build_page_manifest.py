#!/usr/bin/env python3
"""Inventory every editorial PDF page and matching extracted image resources."""
from pathlib import Path
import json, re
from pypdf import PdfReader

pdfs=Path('PDF'); images=Path('9781669952961NIMAS_reconstruccion/images'); rows=[]
for pdf in sorted(pdfs.glob('*_hi.pdf')):
 m=re.search(r'_(L\d\d|FM|EM)_(\d{3})-(\d{3})_',pdf.name)
 if not m: continue
 section,start,end=m.group(1),int(m.group(2)),int(m.group(3)); count=len(PdfReader(str(pdf)).pages)
 for offset in range(count):
  page=start+offset; folder='FM' if section=='FM' else section
  assets=sorted('images/'+str(x.relative_to(images)) for x in (images/folder).glob(f'*_p{page:03d}_*.png')) if (images/folder).exists() else []
  rows.append({'section':section,'pdf':pdf.name,'pdf_index':offset+1,'printed_page':page,'images':assets})
Path('nimas-review/page-manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(len(rows),'PDF pages mapped')
