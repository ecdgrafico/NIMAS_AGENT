#!/usr/bin/env python3
"""Normalize residual bodymatter level wrappers without changing visible text."""
import argparse, re
from pathlib import Path
from lxml import etree

NS = 'http://www.daisy.org/z3986/2005/dtbook/'
Q = lambda n: '{%s}%s' % (NS, n)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('xml',type=Path); args=ap.parse_args()
    t=etree.parse(str(args.xml),etree.XMLParser(remove_blank_text=True))
    for level in list(t.xpath('//d:bodymatter//d:level3',namespaces={'d':NS})):
        if level.find(Q('h3')) is not None: continue
        parent=level.getparent(); pos=parent.index(level)
        first=next((c for c in level if etree.QName(c).localname=='p'),None)
        value=' '.join(''.join(first.itertext()).split()) if first is not None else ''
        m=re.match(r'^([A-Z])(?:[.)]|\s+)(.+)$',value,re.S)
        if m and first is not None:
            h=etree.Element(Q('h3')); h.text=f'{m.group(1)}. {m.group(2).strip()}'
            level.remove(first); level.insert(0,h)
        else:
            for child in list(level):
                level.remove(child); parent.insert(pos,child); pos+=1
            parent.remove(level) if level.getparent() is parent else None
    raw=etree.tostring(t,xml_declaration=True,encoding='UTF-8',pretty_print=True).decode()
    args.xml.write_text('\n'.join(x.lstrip(' \t') for x in raw.splitlines())+'\n',encoding='utf-8')

if __name__=='__main__': main()
