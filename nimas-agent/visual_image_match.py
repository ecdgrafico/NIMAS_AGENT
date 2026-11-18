#!/usr/bin/env python3
"""Content-based matcher for legacy XML image anchors and new 300-DPI PNGs.

It never assumes file order.  Matches are constrained to the PDF page of an
anchor and scored from normalized grayscale pixels; only confident unique
matches are eligible for XML replacement.
"""
import argparse, json, re
from pathlib import Path
from lxml import etree
from PIL import Image, ImageOps, ImageChops, ImageStat

NS='http://www.daisy.org/z3986/2005/dtbook/'
PAGE=re.compile(r'_p(\d{3})_')

def norm(path):
    im=Image.open(path).convert('RGBA')
    bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im)
    im=ImageOps.grayscale(bg.convert('RGB')).resize((48,48),Image.Resampling.LANCZOS)
    # Remove brightness differences so the score describes image content.
    hist=ImageStat.Stat(im); mean=hist.mean[0] or 1
    return Image.eval(im,lambda p:max(0,min(255,int((p-mean)*1.4+128))))

def score(a,b):
    return ImageStat.Stat(ImageChops.difference(a,b)).mean[0]

def page_of(img):
    p=img.xpath('preceding::d:pagenum[@page="normal"][1]',namespaces={'d':NS})
    return int(''.join(p[0].itertext()).strip()) if p else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('package',type=Path);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--apply',action='store_true');ap.add_argument('--apply-review',action='store_true',help='apply best same-page visual candidate and log it for later audit');a=ap.parse_args()
    xml=next(a.package.glob('*.xml'));tree=etree.parse(str(xml));root=tree.getroot();ns={'d':root.nsmap[None]}
    all_new={}
    for f in (a.package/'images').rglob('*.png'):
        m=PAGE.search(f.name)
        if m: all_new.setdefault(int(m.group(1)),[]).append(f)
    cache={}
    def image(p):
        if p not in cache: cache[p]=norm(p)
        return cache[p]
    report={'matches':[],'unmatched':[],'pages':{}}
    used=set()
    for old in tree.xpath('//d:img[starts-with(@src,"images/u")]',namespaces=ns):
        src=old.get('src')
        # The reconstruction intentionally contains only new assets; legacy
        # raster files remain in the untouched original package for comparison.
        legacy=(a.package/src)
        if not legacy.is_file(): legacy=a.package.parent/'9781669952961NIMAS_original'/src
        page=page_of(old)
        candidates=[x for x in all_new.get(page,[]) if str(x) not in used]
        if not legacy.is_file() or not candidates:
            report['unmatched'].append({'src':src,'page':page,'reason':'legacy-or-candidate-missing'});continue
        old_im=image(legacy)
        ranked=sorted((score(old_im,image(x)),x) for x in candidates)
        best,bfile=ranked[0]; runner=ranked[1][0] if len(ranked)>1 else 255
        margin=runner-best
        item={'src':src,'page':page,'new':str(bfile.relative_to(a.package)),'score':round(best,2),'margin':round(margin,2)}
        # Conservative threshold: same extracted visual is normally much lower
        # than an unrelated picture, and must also win over the next candidate.
        if best <= 42 and margin >= 4:
            item['status']='matched';used.add(str(bfile))
            if a.apply:
                old.set('src',str(bfile.relative_to(a.package)))
                old.set('alt','')
                old.set('id',bfile.stem+'_id')
        elif a.apply_review:
            item['status']='mapped-review';used.add(str(bfile))
            old.set('src',str(bfile.relative_to(a.package)))
            old.set('alt','')
            old.set('id',bfile.stem+'_id')
        else: item['status']='review'
        report['matches'].append(item)
    for page,files in all_new.items():
        report['pages'][str(page)]={'unplaced_new':[str(x.relative_to(a.package)) for x in files if str(x) not in used]}
    if a.apply or a.apply_review:
        raw=etree.tostring(tree,xml_declaration=True,encoding='UTF-8',pretty_print=True).decode('UTF-8')
        xml.write_text('\n'.join(line.lstrip(' \t') for line in raw.splitlines())+'\n',encoding='UTF-8')
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2),encoding='UTF-8')
    counts={}
    for x in report['matches']:counts[x['status']]=counts.get(x['status'],0)+1
    print(counts, 'unmatched',len(report['unmatched']))
if __name__=='__main__':main()
