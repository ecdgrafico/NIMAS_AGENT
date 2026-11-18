#!/usr/bin/env python3
"""Conservative structural baseline for L03–L24.

This creates one lesson level1 and topic/activity levels without changing
visible instructional text.  It deliberately leaves detailed PDF image maps
to the per-lesson visual pass.
"""
from lxml import etree
from pathlib import Path
import re

NS='http://www.daisy.org/z3986/2005/dtbook/'
Q=lambda n:f'{{{NS}}}{n}'
ACT=re.compile(r'^([A-E])(?:[.\s]+)(.{4,})$',re.S)
RANGES={2:(13,24), **{n:(25+(n-3)*12, 36+(n-3)*12) for n in range(3,23)}, 23:(265,274), 24:(275,286)}

def txt(e): return ''.join(e.itertext()).strip()
def direct_page(e):
    for x in e:
        if etree.QName(x).localname=='pagenum' and x.get('page')=='normal' and txt(x).isdigit(): return int(txt(x))
    return None
def retag_depth(e,delta):
    for x in [e,*list(e.iterdescendants())]:
        name=etree.QName(x).localname
        if name.startswith('level') and name[5:].isdigit(): x.tag=Q(f'level{min(6,int(name[5:])+delta)}')
        elif name.startswith('h') and name[1:].isdigit(): x.tag=Q(f'h{min(6,int(name[1:])+delta)}')
def first_heading(e):
    return next((x for x in e if etree.QName(x).localname in {'h1','h2','h3','h4','h5','h6'}),None)
def split_direct(level):
    depth=int(etree.QName(level).localname[5:])
    if depth>=6:return
    starts=[]
    for i,x in enumerate(list(level)):
        if etree.QName(x).localname=='p':
            m=ACT.match(txt(x))
            if m: starts.append((i,m))
    for i,m in reversed(starts):
        p=list(level)[i]
        if p.getparent() is not level:continue
        new=etree.Element(Q(f'level{depth+1}')); h=etree.SubElement(new,Q(f'h{depth+1}')); h.text=f'{m.group(1)}. {m.group(2)}'
        pos=level.index(p);level.remove(p)
        while pos<len(level):
            candidate=level[pos];name=etree.QName(candidate).localname
            cm=ACT.match(txt(candidate)) if name=='p' else None
            if (cm is not None) or name==f'level{depth+1}':break
            new.append(candidate)
        level.insert(pos,new)

def main():
    path=Path('9781669952961NIMAS_reconstruccion/9781669952961NIMAS.xml')
    tree=etree.parse(str(path),etree.XMLParser(remove_blank_text=True));body=tree.find('.//'+Q('bodymatter'))
    for lesson in range(3,25):
        start,end=RANGES[lesson]
        children=list(body)
        target=next((x for x in children if etree.QName(x).localname=='level1' and direct_page(x)==start),None)
        if target is None: continue
        # A source may create a fresh level1 at later pages.  Merge it under
        # this lesson until the next lesson starts.
        for sibling in list(body)[body.index(target)+1:]:
            page=direct_page(sibling)
            if etree.QName(sibling).localname=='level1' and page==RANGES.get(lesson+1,(10**9,))[0]: break
            if etree.QName(sibling).localname!='level1': continue
            if page is not None and not (start < page <= end): continue
            retag_depth(sibling,1); sibling.tag=Q('level2')
            h=first_heading(sibling)
            if h is not None: h.tag=Q('h2')
            else:
                # Keep a valid leading heading without fabricating prose.
                p=next((x for x in sibling if etree.QName(x).localname=='p' and txt(x)),None)
                if p is not None:
                    p.tag=Q('h2')
            body.remove(sibling);target.append(sibling)
        h1=first_heading(target)
        if h1 is None:
            lesson_p=next((x for x in target if etree.QName(x).localname=='p' and txt(x)==f'Lesson {lesson}'),None)
            if lesson_p is not None: lesson_p.tag=Q('h1')
        elif etree.QName(h1).localname!='h1': h1.tag=Q('h1')
        for topic in [x for x in target if etree.QName(x).localname=='level2']:
            split_direct(topic)
    # DTBook levels require body content after the heading; retain an explicit
    # empty paragraph when a source activity contains no captured body text.
    for level in tree.xpath('//d:level3 | //d:level4 | //d:level5 | //d:level6', namespaces={'d':NS}):
        if len(level)==1 and etree.QName(level[0]).localname.startswith('h'):
            etree.SubElement(level,Q('p'))
    raw=etree.tostring(tree,encoding='UTF-8',xml_declaration=True,pretty_print=True).decode()
    path.write_text('\n'.join(line.lstrip(' \t') for line in raw.splitlines())+'\n',encoding='utf-8')
if __name__=='__main__':main()
