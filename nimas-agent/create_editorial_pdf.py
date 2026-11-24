#!/usr/bin/env python3
"""Create editable cover, title-page and copyright-page PDF evidence.

The generated PDF is a project artifact only; it never overwrites source PDFs
and still requires human review before it can become approved frontmatter.
"""
import argparse, json
from pathlib import Path
import fitz

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    root=args.project.resolve()
    metadata=json.loads((root/"metadata/nimac.json").read_text(encoding="utf-8"))
    title=str(metadata.get("title") or root.name)
    creators=metadata.get("creators") or []
    if isinstance(creators,list):
        creators=", ".join(str(value.get("name", "")) if isinstance(value,dict) else str(value) for value in creators)
    else:
        creators=str(creators)
    publisher=str(metadata.get("publisher") or "")
    identifier=str(metadata.get("identifier") or "")
    year=str(metadata.get("copyright_year") or metadata.get("publication_year") or "")
    output=(args.output or root/"working"/"generated-frontmatter.pdf").resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    doc=fitz.open()
    pages=[
        ("COVER", title, creators),
        ("TITLE PAGE", title, creators),
        ("COPYRIGHT", f"{title}\\n{publisher}", f"ISBN / identifier: {identifier}\\nCopyright: {year}"),
    ]
    for heading,main,detail in pages:
        page=doc.new_page(width=612,height=792)
        page.insert_text((72,120),heading,fontsize=14,fontname="helv")
        page.insert_textbox((72,220,540,360),main,fontsize=26,align=1)
        page.insert_textbox((72,390,540,500),detail,fontsize=13,align=1)
    doc.save(output)
    report={"status":"generated","path":str(output),"pages":3,"review_required":True}
    (output.with_suffix(".json")).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
