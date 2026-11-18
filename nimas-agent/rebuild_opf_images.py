#!/usr/bin/env python3
from pathlib import Path
from lxml import etree
pkg=Path('9781669952961NIMAS_reconstruccion');opf=pkg/'9781669952961NIMAS.opf'
t=etree.parse(str(opf));r=t.getroot(); ns={'o':r.nsmap.get(None)};manifest=t.xpath('//o:manifest',namespaces=ns)[0]
for item in list(manifest):
 if item.get('media-type','').startswith('image/'):
  manifest.remove(item)
for image in sorted((pkg/'images').rglob('*.png')):
 href='images/'+str(image.relative_to(pkg/'images')); ident='img_'+image.stem.replace('-','_')
 etree.SubElement(manifest,'{'+r.nsmap.get(None)+'}item',id=ident,href=href,**{'media-type':'image/png'})
etree.indent(t,space='',level=0);t.write(str(opf),encoding='UTF-8',xml_declaration=True)
