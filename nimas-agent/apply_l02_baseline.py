#!/usr/bin/env python3
"""Install the independently page-mapped L02 tree into the progressive package."""
from copy import deepcopy
from lxml import etree

target='9781669952961NIMAS_revision_l02_em/9781669952961NIMAS.xml'
source='9781669952961NIMAS_corregido/9781669952961NIMAS.xml'
t=etree.parse(target); s=etree.parse(source); ns={'d':t.getroot().nsmap[None]}
b=t.xpath('//d:bodymatter',namespaces=ns)[0]; sb=s.xpath('//d:bodymatter',namespaces=ns)[0]
replacement=deepcopy(sb.xpath('./d:level1[2]',namespaces=ns)[0])
for child in list(b):
    pages=[]
    for p in child.xpath('.//d:pagenum[@page="normal"]',namespaces=ns):
        try: pages.append(int(''.join(p.itertext()).strip()))
        except ValueError: pass
    if pages and min(pages)>=13 and max(pages)<=24:
        b.remove(child)
b.insert(1,replacement)
etree.indent(t,space='',level=0)
t.write(target,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
