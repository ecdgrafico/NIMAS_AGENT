#!/usr/bin/env python3
"""Restore EM page anchors 296–297 from the editorial PDF sequence."""
import argparse
from pathlib import Path
from lxml import etree

NS='http://www.daisy.org/z3986/2005/dtbook/'
Q=lambda n:'{%s}%s'%(NS,n)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('xml',type=Path); args=ap.parse_args()
    t=etree.parse(str(args.xml),etree.XMLParser(remove_blank_text=True))
    rm=t.xpath('//d:rearmatter',namespaces={'d':NS})[0]
    tail=rm.xpath('./d:level1[last()]',namespaces={'d':NS})[0]
    existing={''.join(x.itertext()).strip() for x in rm.xpath('.//d:pagenum[@page="normal"]',namespaces={'d':NS})}
    for n in ('296','297'):
        if n not in existing:
            p=etree.Element(Q('pagenum'),id=f'page-{n}',page='normal'); p.text=n; tail.append(p)
    raw=etree.tostring(t,xml_declaration=True,encoding='UTF-8',pretty_print=True).decode()
    args.xml.write_text('\n'.join(x.lstrip(' \t') for x in raw.splitlines())+'\n',encoding='utf-8')

if __name__=='__main__': main()
