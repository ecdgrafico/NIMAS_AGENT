#!/usr/bin/env python3
"""Remove inherited invalid image references from a working NIMAS package.

This is intentionally conservative: it removes only legacy image paths and
their empty containers. It does not invent replacement images or text.
"""
import argparse
from pathlib import Path
from lxml import etree

DT = "http://www.daisy.org/z3986/2005/dtbook/"
OEB = "http://openebook.org/namespaces/oeb-package/1.0/"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path)
    args = ap.parse_args()
    pkg = args.package
    xml_path = next(pkg.glob("*.xml"))
    opf_path = next(pkg.glob("*.opf"))
    xml = etree.parse(str(xml_path), etree.XMLParser(remove_blank_text=True))
    removed = []
    for img in list(xml.xpath("//d:img", namespaces={"d": DT})):
        src = img.get("src", "")
        if src.startswith(("images/u", "images/fm/", "images/em/")):
            removed.append(src)
            parent = img.getparent()
            parent.remove(img)
            if etree.QName(parent).localname == "imggroup" and len(parent) == 0:
                parent.getparent().remove(parent)
    raw = etree.tostring(xml, xml_declaration=True, encoding="UTF-8", pretty_print=True).decode()
    xml_path.write_text("\n".join(x.lstrip(" \t") for x in raw.splitlines()) + "\n", encoding="utf-8")

    opf = etree.parse(str(opf_path), etree.XMLParser(remove_blank_text=True))
    for item in list(opf.xpath("//o:item", namespaces={"o": OEB})):
        href = item.get("href", "")
        if href.startswith(("images/u", "images/fm/", "images/em/")):
            item.getparent().remove(item)
    raw = etree.tostring(opf, xml_declaration=True, encoding="UTF-8", pretty_print=True).decode()
    opf_path.write_text("\n".join(x.lstrip(" \t") for x in raw.splitlines()) + "\n", encoding="utf-8")
    print(f"removed_xml_refs={len(removed)}")
    print(f"unique_paths={len(set(removed))}")

if __name__ == "__main__":
    main()
