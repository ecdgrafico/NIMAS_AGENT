#!/usr/bin/env python3
"""Align end-matter anchors to editorial PDF pagination; omit blank tail."""
from lxml import etree
p='9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml';ns='{http://www.daisy.org/z3986/2005/dtbook/}'
t=etree.parse(p);r=t.getroot();n={'d':r.nsmap[None]}
for x in t.xpath('//d:rearmatter//d:pagenum[@page="normal"]',namespaces=n):
 value=''.join(x.itertext()).strip()
 if not value.isdigit():continue
 old=int(value);new=old+9
 if 278<=old<=295:
  x.text=str(new);x.set('id',f'page-{new}')
  if new>=298:
   # Blank production pages are intentionally not represented.
   x.getparent().remove(x)
etree.indent(t,space='',level=0);t.write(p,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
