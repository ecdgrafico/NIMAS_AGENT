#!/usr/bin/env python3
"""Install one page-mapped lesson tree after its PDF review is complete."""
import argparse
from copy import deepcopy
from lxml import etree

p=argparse.ArgumentParser();p.add_argument('lesson',type=int);p.add_argument('start',type=int);p.add_argument('end',type=int);a=p.parse_args()
target='9781669952961NIMAS_revision_l02_em/9781669952961NIMAS.xml'; source='9781669952961NIMAS_corregido/9781669952961NIMAS.xml'
t=etree.parse(target);s=etree.parse(source);ns={'d':t.getroot().nsmap[None]};b=t.xpath('//d:bodymatter',namespaces=ns)[0];sb=s.xpath('//d:bodymatter',namespaces=ns)[0]
replacement=deepcopy(sb.xpath(f'./d:level1[{a.lesson}]',namespaces=ns)[0])
for child in list(b):
 nums=[]
 for q in child.xpath('.//d:pagenum[@page="normal"]',namespaces=ns):
  try: nums.append(int(''.join(q.itertext()).strip()))
  except ValueError: pass
 if nums and min(nums)>=a.start and max(nums)<=a.end: b.remove(child)
b.insert(a.lesson-1,replacement); etree.indent(t,space='',level=0); t.write(target,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
