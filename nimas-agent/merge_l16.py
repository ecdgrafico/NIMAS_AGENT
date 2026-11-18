#!/usr/bin/env python3
"""Merge L16 page wrappers into the approved lesson/topic/activity hierarchy."""
import re
from lxml import etree
p='9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml';ns='{http://www.daisy.org/z3986/2005/dtbook/}'
t=etree.parse(p);r=t.getroot();n={'d':r.nsmap[None]};body=t.xpath('//d:bodymatter',namespaces=n)[0]
def root_for(page):
 x=t.xpath(f'//d:pagenum[normalize-space()="{page}"]',namespaces=n)[0]
 while etree.QName(x.getparent()).localname!='bodymatter':x=x.getparent()
 return x
lesson=root_for(181)
for page in [185,188,189,191]:
 section=root_for(page); body.remove(section); section.tag=ns+'level2'
 h=section.find(ns+'h1')
 if h is None:
  h=etree.Element(ns+'h2');section.insert(0,h)
 else:h.tag=ns+'h2'
 # page wrappers used level2 for every subpart; sections require level3.
 for child in list(section):
  if etree.QName(child).localname=='level2':
   child.tag=ns+'level3'; head=child.find(ns+'h2')
   if head is not None:
    value=''.join(head.itertext()).strip();head.tag=ns+'h3'
    if re.match(r'^[A-Z]$',value):head.text=value+'.'
 lesson.append(section)
# A reader's named subblocks are children of its activity level, so they use
# the next structural depth rather than a second level3.
for nested in lesson.xpath('.//d:level3/d:level3',namespaces=n):
 nested.tag=ns+'level4'
 head=nested.find(ns+'h3')
 if head is not None: head.tag=ns+'h4'
etree.indent(t,space='',level=0);t.write(p,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
