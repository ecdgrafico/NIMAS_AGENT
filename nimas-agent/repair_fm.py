#!/usr/bin/env python3
from lxml import etree
p='9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml';ns='{http://www.daisy.org/z3986/2005/dtbook/}'
t=etree.parse(p);r=t.getroot();n={'d':r.nsmap[None]};f=t.xpath('//d:frontmatter',namespaces=n)[0]
for img in f.xpath('.//d:img',namespaces=n):
 img.set('src','images/FM/PHE27_SE_FM_pi_01.png');img.set('id','PHE27_SE_FM_pi_01_id');img.set('alt','')
for pg in list(f.xpath('.//d:pagenum[normalize-space()="viii"]',namespaces=n)):
 pg.getparent().remove(pg)
etree.indent(t,space='',level=0);t.write(p,encoding='UTF-8',xml_declaration=True,doctype=t.docinfo.doctype)
