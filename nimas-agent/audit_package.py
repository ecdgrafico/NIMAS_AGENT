#!/usr/bin/env python3
"""Fail-closed preflight for a PDF-led NIMAS correction package."""
import argparse, json, re, sys
from pathlib import Path
from lxml import etree

def issue(code, detail, severity="error"): return {"severity": severity, "code": code, "detail": detail}
def tag(x): return etree.QName(x).localname

def main():
 p=argparse.ArgumentParser(); p.add_argument("package", type=Path); p.add_argument("--report", type=Path, required=True); a=p.parse_args()
 xmls=list(a.package.glob('*.xml')); findings=[]
 if len(xmls)!=1: findings.append(issue('xml-count', f'Expected one XML, found {len(xmls)}')); return write(a.report, findings)
 try: tree=etree.parse(str(xmls[0]))
 except etree.XMLSyntaxError as e: return write(a.report,[issue('xml-parse',str(e))])
 root=tree.getroot(); ns={'d':root.nsmap.get(None)}
 nums=[]
 for x in tree.xpath('//d:pagenum[@page="normal"]',namespaces=ns):
  try: nums.append(int(''.join(x.itertext()).strip()))
  except ValueError: findings.append(issue('pagenum-text',f'Non-numeric normal pagenum at line {x.sourceline}'))
 expected=set(range(1,298)); missing=sorted(expected-set(nums))
 if missing: findings.append(issue('missing-page-anchors',f'Missing normal pagenum anchors: {missing}'))
 if any(b<=a for a,b in zip(nums,nums[1:])): findings.append(issue('page-order', 'Normal pagenum anchors are not strictly increasing'))
 for x in tree.xpath('//d:img',namespaces=ns):
  src=x.get('src',''); match=re.search(r'_p(\d{3})_',src)
  if not (a.package/src).is_file(): findings.append(issue('missing-image',src))
  if match:
   prev=x.xpath('preceding::d:pagenum[@page="normal"][1]',namespaces=ns)
   if prev and int(match.group(1)) != int(''.join(prev[0].itertext()).strip()): findings.append(issue('image-page-mismatch',f'{src} follows pagenum {"".join(prev[0].itertext()).strip()}'))
 ids=[x.get('id') for x in tree.xpath('//*[@id]')]; dup=sorted({x for x in ids if ids.count(x)>1})
 if dup: findings.append(issue('duplicate-id', ', '.join(dup[:10])))
 for level,head in [('level1','h1'),('level2','h2'),('level3','h3'),('level4','h4')]:
  for x in tree.xpath(f'//d:bodymatter//d:{level}',namespaces=ns):
   if not x.xpath(f'./d:{head}',namespaces=ns): findings.append(issue('level-heading',f'{level} line {x.sourceline} lacks direct {head}'))
 for x in tree.xpath('//d:imggroup[not(d:img)]',namespaces=ns): findings.append(issue('empty-imggroup',f'line {x.sourceline}'))
 write(a.report,findings)

def write(path, findings):
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps({'status':'blocked' if findings else 'pass','findings':findings},indent=2),encoding='utf-8')
 print(f'{len(findings)} finding(s): {path}')
 sys.exit(1 if findings else 0)
if __name__=='__main__': main()
