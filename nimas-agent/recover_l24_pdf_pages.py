#!/usr/bin/env python3
"""Recover L24 pages absent from source XML from the editorial PDF."""
from pathlib import Path
from lxml import etree
from pypdf import PdfReader
import re

package=Path('9781669952961NIMAS_revision_l02_em'); xml=package/'9781669952961NIMAS.xml'; pdf=Path('PDF/PHE27_SE_L24_275-286_hi.pdf'); ns='{http://www.daisy.org/z3986/2005/dtbook/}'
t=etree.parse(str(xml)); root=t.getroot(); n={'d':root.nsmap[None]}; body=t.xpath('//d:bodymatter',namespaces=n)[0]; lesson=body.xpath('./d:level1[24]',namespaces=n)[0]
existing={int(''.join(x.itertext()).strip()) for x in lesson.xpath('.//d:pagenum[@page="normal"]',namespaces=n) if ''.join(x.itertext()).strip().isdigit()}
reader=PdfReader(str(pdf))
for number,page in enumerate(reader.pages,275):
 if number < 278 or number in existing: continue
 pnum=etree.SubElement(lesson,ns+'pagenum',id=f'page-{number}',page='normal');pnum.text=str(number)
 raw=' '.join((page.extract_text() or '').split())
 raw=re.sub(r'PHE27_SE_L24_275-286\.indd.*','',raw)
 raw=re.sub(r'© by Vista Higher Learning, Inc\. All rights reserved\.', '',raw)
 raw=re.sub(r'NameName DateDate|LESSON 24|Lesson 24', '',raw)
 raw=re.sub(r'\s+',' ',raw).strip()
 if raw:
  para=etree.SubElement(lesson,ns+'p');para.text=raw
 for image in sorted((package/'images'/'L24').glob(f'*_p{number:03d}_*.png')):
  group=etree.SubElement(lesson,ns+'imggroup'); stem=image.stem
  etree.SubElement(group,ns+'img',id=f'{stem}_id',src='images/L24/'+image.name,alt='')
etree.indent(t,space='',level=0);t.write(str(xml),encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
