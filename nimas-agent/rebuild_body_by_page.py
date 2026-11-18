#!/usr/bin/env python3
"""Create one clean level1 per printed lesson from the original page sequence."""
from copy import deepcopy
from lxml import etree

path='9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml'; ns='{http://www.daisy.org/z3986/2005/dtbook/}'
t=etree.parse(path); root=t.getroot(); n={'d':root.nsmap[None]}; body=t.xpath('//d:bodymatter',namespaces=n)[0]
source=list(body)
def pages(node):
 out=[]
 for x in node.xpath('.//d:pagenum[@page="normal"]',namespaces=n):
  try: out.append(int(''.join(x.itertext()).strip()))
  except ValueError: pass
 return out
def add_contents(target,node):
 # Page wrappers are conversion artifacts. Keep their editorial descendants,
 # never their duplicate outer lesson level/headline.
 for child in node:
  if etree.QName(child).localname=='h1': continue
  target.append(deepcopy(child))
for child in list(body): body.remove(child)
ranges=[(i,1+(i-1)*12,12+(i-1)*12) for i in range(1,23)]+[(23,265,274),(24,275,286)]
for lesson,start,end in ranges:
 level=etree.SubElement(body,ns+'level1'); h=etree.SubElement(level,ns+'h1');h.text=f'Lesson {lesson}'
 for node in source:
  p=pages(node)
  if p and min(p)>=start and max(p)<=end: add_contents(level,node)
etree.indent(t,space='',level=0);t.write(path,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
