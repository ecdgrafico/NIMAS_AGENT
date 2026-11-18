#!/usr/bin/env python3
"""Rebuild DTBook lesson hierarchy from the untouched XML, PDF page ranges, and approved L01 rules.

Images are deliberately preserved as source placeholders; image replacement is
outside this reconstruction pass.
"""
from copy import deepcopy
from lxml import etree
from pathlib import Path
import re
NS='http://www.daisy.org/z3986/2005/dtbook/'
Q=lambda n:f'{{{NS}}}{n}'
ACT=re.compile(r'^([A-E])(?:[.\s]+)(.{4,})$',re.S)
RANGES={1:(1,12),2:(13,24),**{n:(25+(n-3)*12,36+(n-3)*12) for n in range(3,23)},23:(265,274),24:(275,286)}
def name(x):return etree.QName(x).localname
def text(x):return ''.join(x.itertext()).strip()
def page(x):
 p=x.xpath('.//d:pagenum[@page="normal"][1]',namespaces={'d':NS})
 return int(text(p[0])) if p and text(p[0]).isdigit() else None
def retag_children(root,delta):
 for x in root.iterdescendants():
  n=name(x)
  if n.startswith('level') and n[5:].isdigit():x.tag=Q(f'level{min(6,int(n[5:])+delta)}')
  elif n.startswith('h') and n[1:].isdigit():x.tag=Q(f'h{min(6,int(n[1:])+delta)}')
def first_direct_heading(x):return next((c for c in x if re.fullmatch(r'h[1-6]',name(c))),None)
def split_activities(level):
 depth=int(name(level)[5:]);starts=[]
 for idx,c in enumerate(list(level)):
  if name(c)=='p':
   m=ACT.match(text(c))
   if m:starts.append((idx,m))
 for _,m in reversed(starts):
  p=next((c for c in level if name(c)=='p' and ACT.match(text(c)) and ACT.match(text(c)).group(1)==m.group(1) and text(c)==m.group(0)),None)
  if p is None:continue
  node=etree.Element(Q(f'level{min(6,depth+1)}'));h=etree.SubElement(node,Q(f'h{min(6,depth+1)}'));h.text=f'{m.group(1)}. {m.group(2)}'
  at=level.index(p);level.remove(p)
  while at<len(level):
   c=level[at];cm=ACT.match(text(c)) if name(c)=='p' else None
   if cm or name(c)==name(node):break
   node.append(c)
  if len(node)==1:etree.SubElement(node,Q('p'))
  level.insert(at,node)
def fix_nested_depth(level):
 parent_depth=int(name(level)[5:])
 for child in list(level):
  if name(child).startswith('level') and name(child)[5:].isdigit():
   child_depth=int(name(child)[5:])
   if child_depth<=parent_depth:
    retag_children(child,parent_depth+1-child_depth);child.tag=Q(f'level{parent_depth+1}')
    h=first_direct_heading(child)
    if h is not None:h.tag=Q(f'h{parent_depth+1}')
   fix_nested_depth(child)
def main():
 dest=Path('9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml')
 src=Path('9781669952961NIMAS_original/9781669952961NIMAS.xml')
 out=etree.parse(str(dest),etree.XMLParser(remove_blank_text=True)); source=etree.parse(str(src),etree.XMLParser(remove_blank_text=True))
 body=out.find('.//'+Q('bodymatter')); source_body=source.find('.//'+Q('bodymatter'))
 source_pages=[deepcopy(x) for x in source_body if page(x) is not None]
 # Replace only bodymatter.  FM/EM work in the reconstruction stays intact.
 for x in list(body):body.remove(x)
 for lesson,(lo,hi) in RANGES.items():
  pieces=[x for x in source_pages if (page(x) or -1)>=lo and (page(x) or -1)<=hi]
  if not pieces:continue
  root=etree.Element(Q('level1'))
  current=None
  for i,piece in enumerate(pieces):
   heading=first_direct_heading(piece)
   lesson_label=next((x for x in piece if name(x)=='p' and text(x)==f'Lesson {lesson}'),None)
   if i==0:
    # First page establishes the lesson root and keeps all printed intro text.
    for c in list(piece):root.append(c)
    existing_h1=next((x for x in root if name(x)=='h1'),None)
    if lesson_label is not None:lesson_label.tag=Q('h1')
    elif existing_h1 is None:
     h=etree.Element(Q('h1'));h.text=f'Lesson {lesson}';root.insert(1,h)
    elif text(existing_h1)!=f'Lesson {lesson}':
     # A topical h1 on the opening page belongs below the lesson title.
     existing_h1.tag=Q('p');h=etree.Element(Q('h1'));h.text=f'Lesson {lesson}';root.insert(1,h)
    continue
   if heading is not None:
    retag_children(piece,1);piece.tag=Q('level2');heading.tag=Q('h2');root.append(piece);current=piece
   elif current is not None:
    for c in list(piece):current.append(c)
   else:
    # A continuation before the first explicit topic remains lesson content.
    for c in list(piece):root.append(c)
  for topic in [x for x in root if name(x)=='level2']:
   split_activities(topic)
  fix_nested_depth(root)
  # DTBook allows exactly one h1 in a level1.  Source conversion sometimes
  # emits a page-topic h1 inside the opening-page capture; preserve its text
  # as body text rather than leaving an invalid second document-level heading.
  # Enforce the approved book convention: the only h1 is “Lesson N”.
  wanted=f'Lesson {lesson}'
  chosen=next((x for x in root if name(x) in {'p','h1'} and text(x)==wanted),None)
  for child in root:
   if name(child)=='h1' and child is not chosen: child.tag=Q('p')
  if chosen is not None: chosen.tag=Q('h1')
  else:
   h=etree.Element(Q('h1'));h.text=wanted
   first_page=next((i for i,x in enumerate(root) if name(x)=='pagenum'),-1)
   root.insert(first_page+1,h)
  body.append(root)
 raw=etree.tostring(out,xml_declaration=True,encoding='UTF-8',pretty_print=True).decode()
 dest.write_text('\n'.join(line.lstrip(' \t') for line in raw.splitlines())+'\n',encoding='UTF-8')
if __name__=='__main__':main()
