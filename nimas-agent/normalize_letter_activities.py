#!/usr/bin/env python3
"""Promote direct lettered activity sections to level3 under their topic."""
import re
from lxml import etree
p='9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml';ns='{http://www.daisy.org/z3986/2005/dtbook/}'
t=etree.parse(p);r=t.getroot();n={'d':r.nsmap[None]}
for lesson in t.xpath('//d:bodymatter/d:level1',namespaces=n):
 host=None
 for child in list(lesson):
  if etree.QName(child).localname!='level2':continue
  h=child.find(ns+'h2');label=''.join(h.itertext()).strip() if h is not None else ''
  if not re.fullmatch(r'[A-M]',label):host=child;continue
  if host is None:continue
  child.tag=ns+'level3';h.tag=ns+'h3';h.text=label+'.'
  lesson.remove(child);host.append(child)
etree.indent(t,space='',level=0);t.write(p,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
