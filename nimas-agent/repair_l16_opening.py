#!/usr/bin/env python3
"""Apply the approved L01 hierarchy to L16 pp. 181–184."""
from lxml import etree
path='9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml'; ns='{http://www.daisy.org/z3986/2005/dtbook/}'
t=etree.parse(path);root=t.getroot();n={'d':root.nsmap[None]};p181=t.xpath('//d:pagenum[normalize-space()="181"]',namespaces=n)[0]; lesson=p181
while etree.QName(lesson.getparent()).localname!='bodymatter':lesson=lesson.getparent()
# Existing printed title becomes the one level1 heading.
title=lesson[2]; title.tag=ns+'h1'; lesson.remove(title);lesson.insert(0,title)
# Existing printed topical label becomes h2; retain all following page content.
topic_start=next(i for i,x in enumerate(lesson) if etree.QName(x).localname=='p' and ''.join(x.itertext()).strip()=='ooVowel Diphthong')
topic=etree.Element(ns+'level2'); heading=etree.SubElement(topic,ns+'h2');heading.text='Vowel Diphthong oo'
for node in list(lesson)[topic_start:]:
 lesson.remove(node); topic.append(node)
lesson.append(topic)
# Lettered activities are activities, not peer topical sections.
for node in list(topic):
 if etree.QName(node).localname=='level2':
  h=node.find(ns+'h2'); value=''.join(h.itertext()).strip() if h is not None else ''
  if value in 'ABCDE':
   node.tag=ns+'level3';h.tag=ns+'h3';h.text=value+'.'
etree.indent(t,space='',level=0);t.write(path,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
