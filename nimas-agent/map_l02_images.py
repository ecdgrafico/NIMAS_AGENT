#!/usr/bin/env python3
"""Install visually reviewed 300-DPI L02 image references.

The order here was checked against PDF pages 13–22.  It is deliberately a
lesson-specific map, not a filename-order operation applied to the book.
"""
from lxml import etree
from pathlib import Path

NS = "http://www.daisy.org/z3986/2005/dtbook/"
Q = lambda n: f"{{{NS}}}{n}"
PKG = Path("9781669952961NIMAS_reconstruccion")

def normal_page(img):
    p = img.xpath('preceding::d:pagenum[@page="normal"][1]', namespaces={"d": NS})
    return int(''.join(p[0].itertext()).strip()) if p else None

def group(filename):
    g = etree.Element(Q("imggroup"))
    image = etree.SubElement(g, Q("img"))
    image.set("src", f"images/L02/{filename}")
    image.set("alt", "")
    image.set("id", filename.removesuffix(".png") + "_id")
    return g

def source(page, index):
    return f"PHE27_SE_L02_p{page:03d}_{index:02d}.png"

def after(anchor, item):
    parent = anchor.getparent(); parent.insert(parent.index(anchor) + 1, item)

def direct_activity(topic, letter):
    for x in topic:
        if etree.QName(x).localname == "level3":
            h = x.find(Q("h3"))
            if h is not None and (''.join(h.itertext()).strip().startswith(letter + ".")):
                return x
    raise ValueError(letter)

def main():
    path = PKG / "9781669952961NIMAS.xml"
    tree = etree.parse(str(path), etree.XMLParser(remove_blank_text=True))
    ns = {"d": NS}
    imgs = tree.xpath('//d:img', namespaces=ns)
    bypage = {p: [x for x in imgs if normal_page(x) == p] for p in range(13, 25)}

    # Remove all obsolete 72-DPI images for L02.  They are not allowed to remain.
    for image in [x for xs in bypage.values() for x in xs]:
        parent = image.getparent(); parent.remove(image)
        if not len(parent): parent.getparent().remove(parent)

    # Locate topical containers after the semantic repair.
    levels = tree.xpath('//d:level2', namespaces=ns)
    topic = {}
    for l in levels:
        p = l.find('.//' + Q('pagenum'))
        if p is not None and ''.join(p.itertext()).strip().isdigit(): topic[int(''.join(p.itertext()).strip())] = l

    # p13: story photograph; the former lesson-inventory decorative asset is omitted.
    lesson = tree.xpath('//d:level1[d:pagenum[normalize-space()="13"]]', namespaces=ns)[0]
    story = next(x for x in lesson if etree.QName(x).localname == 'p' and ''.join(x.itertext()).strip().startswith('The cat is named Rod'))
    after(story, group(source(13, 1)))

    # p14–15: word pictures in the visual reading order.
    for page, labels in ((14, [('F f',1), ('fish',2), ('C. Look around.',3), ('fan rug',4)]),
                         (15, [('C c',1), ('cap',2), ('C. Look around.',3), ('car',4)])):
        root = topic[page]
        for needle, idx in labels:
            anchor = next(x for x in root.iter() if etree.QName(x).localname in {'p','h3'} and ''.join(x.itertext()).strip().startswith(needle))
            after(anchor, group(source(page, idx)))

    # p16: two tracing panels, then five B pictures and five C pictures.
    a, b, c = (direct_activity(topic[16], ch) for ch in 'ABC')
    for idx in (1,2): a.append(group(source(16, idx)))
    for idx in range(3,8): b.append(group(source(16, idx)))
    for idx in range(8,13): c.append(group(source(16, idx)))

    # p17 and p18: image groups belong to the respective phonics activity.
    for page, intro, bcount, ccount in ((17, 2, 4, 2), (18, 2, 4, 2)):
        root = topic[page]
        h = root.find(Q('h2'))
        for idx in range(1, intro+1): after(h, group(source(page, idx)))
        b, c = direct_activity(root, 'B'), direct_activity(root, 'C')
        for idx in range(intro+1, intro+bcount+1): b.append(group(source(page, idx)))
        for idx in range(intro+bcount+1, intro+bcount+ccount+1): c.append(group(source(page, idx)))

    # p19: two tracing panels, then five picture prompts for activity B.
    root = topic[19]
    a, b = direct_activity(root, 'A'), direct_activity(root, 'B')
    for idx in (1,2): a.append(group(source(19, idx)))
    for idx in range(3,8): b.append(group(source(19, idx)))

    # p20: one example and four picture prompts, all in exercise A.
    root = topic[19]  # p.20 continues the two-vowel topic begun on p.19.
    for idx in range(1,6): root.append(group(source(20, idx)))

    # Reader panels: four on p21 and three on p22, in story sequence.  They
    # must be inside the story, before activities on pp.23–24.
    reader = topic[21]
    story_level = next(x for x in reader if etree.QName(x).localname == 'level3' and ''.join(x.find(Q('h3')).itertext()).strip() == 'Cam and Rob')
    p22 = next(x for x in story_level if etree.QName(x).localname == 'pagenum' and ''.join(x.itertext()).strip() == '22')
    insert_at = story_level.index(p22)
    for idx in range(1,5):
        story_level.insert(insert_at, group(source(21, idx))); insert_at += 1
    # p22 groups follow the page marker and its table.
    table22 = next(x for x in story_level if etree.QName(x).localname == 'table' and story_level.index(x) > story_level.index(p22))
    insert_at = story_level.index(table22) + 1
    for idx in range(1,4):
        story_level.insert(insert_at, group(source(22, idx))); insert_at += 1

    raw = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', pretty_print=True).decode('utf-8')
    path.write_text('\n'.join(line.lstrip(' \t') for line in raw.splitlines()) + '\n', encoding='utf-8')

if __name__ == '__main__': main()
