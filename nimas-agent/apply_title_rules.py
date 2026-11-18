#!/usr/bin/env python3
"""Apply confirmed mechanical rules derived from the PHE27 L01 review."""
import argparse, re
from pathlib import Path
from lxml import etree

NS='http://www.daisy.org/z3986/2005/dtbook/'
Q=lambda n:'{%s}%s'%(NS,n)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('xml',type=Path); args=ap.parse_args()
    t=etree.parse(str(args.xml),etree.XMLParser(remove_blank_text=True))
    body=t.xpath('//d:bodymatter',namespaces={'d':NS})[0]
    removed=0
    for p in list(body.xpath('.//d:p',namespaces={'d':NS})):
        value=' '.join(''.join(p.itertext()).split())
        if re.fullmatch(r'LESSON\s+\d+',value,re.I) or value.startswith('© by Vista Higher Learning'):
            p.getparent().remove(p); removed+=1
    for x in t.iter():
        if etree.QName(x).localname == 'SPAN' and x.get('class') == 'WOL': x.tag=Q('span')
    raw=etree.tostring(t,xml_declaration=True,encoding='UTF-8',pretty_print=True).decode()
    args.xml.write_text('\n'.join(x.lstrip(' \t') for x in raw.splitlines())+'\n',encoding='utf-8')
    print(f'removed_page_furniture={removed}')

if __name__=='__main__': main()
