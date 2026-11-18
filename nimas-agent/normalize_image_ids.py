#!/usr/bin/env python3
"""Ensure every DTBook image identifier is unique after visual remapping."""
from lxml import etree
from pathlib import Path
from collections import Counter
NS='http://www.daisy.org/z3986/2005/dtbook/'
def main():
 p=Path('9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml');t=etree.parse(str(p));ns={'d':NS};seen=Counter()
 for img in t.xpath('//d:img',namespaces=ns):
  base='img_'+Path(img.get('src','image')).stem+'_id';seen[base]+=1
  img.set('id',base if seen[base]==1 else f'{base}_{seen[base]}')
 raw=etree.tostring(t,xml_declaration=True,encoding='UTF-8',pretty_print=True).decode();p.write_text('\n'.join(x.lstrip(' \t') for x in raw.splitlines())+'\n',encoding='utf-8')
if __name__=='__main__':main()
