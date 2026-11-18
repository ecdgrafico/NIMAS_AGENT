#!/usr/bin/env python3
from lxml import etree
p='9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml';ns='{http://www.daisy.org/z3986/2005/dtbook/}'
t=etree.parse(p);r=t.getroot();n={'d':r.nsmap[None]};q=t.xpath('//d:pagenum[normalize-space()="181"]',namespaces=n)[0];lesson=q
while etree.QName(lesson.getparent()).localname!='bodymatter':lesson=lesson.getparent()
for item in lesson.xpath('.//d:level3/d:level3',namespaces=n):
 item.tag=ns+'level4';h=item.find(ns+'h3')
 if h is not None:h.tag=ns+'h4'
etree.indent(t,space='',level=0);t.write(p,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
