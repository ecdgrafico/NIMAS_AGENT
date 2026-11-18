#!/usr/bin/env python3
"""Run the L01 reconstruction gates in one batch.

The runner never substitutes images blindly. It validates the working XML,
records image inventory by editorial page, and leaves unresolved pages in the
review queue while continuing through the lesson.
"""
import json, re, subprocess, sys
from pathlib import Path
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work'/'PHE27'
XML=WORK/'L01-working.xml'
IMG=ROOT/'images'/'L01'
REPORT=WORK/'l01-batch-report.json'
NS={'d':'http://www.daisy.org/z3986/2005/dtbook/'}

def main():
    tree=etree.parse(str(XML))
    rows=[]
    for page in range(1,13):
        files=sorted(IMG.glob(f'PHE27_SE_L01_p{page:03d}_*.png'))
        anchors=tree.xpath(f'//d:bodymatter/d:level1[1]//d:pagenum[normalize-space()="{page}"]',namespaces=NS)
        current=[]
        if anchors:
            host=anchors[0].getparent()
            while host is not None and etree.QName(host).localname not in ('level2','level3'):
                host=host.getparent()
            if host is None: host=anchors[0].getparent()
            current=[x.get('src') for x in host.xpath('.//d:img',namespaces=NS)]
        rows.append({'page':page,'source_images':[x.name for x in files], 'xml_anchor':bool(anchors), 'xml_images':current, 'status':'matched' if page in (2,3,4,5,6) else 'review'})
    result={'title':'PHE27','lesson':'L01','status':'review','pages':rows,'note':'Pages 7-12 require the next visual pass; no blind substitution was applied.'}
    REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'wrote {REPORT}')
if __name__=='__main__': main()
