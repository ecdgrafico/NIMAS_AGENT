#!/usr/bin/env python3
"""Assemble a PDF-led project into a reviewable NIMAS package.

This exporter is deliberately approval-gated: every classified unit must have
an approved XML fragment in revision/approved before a ZIP can be produced.
"""
import argparse, json, shutil, zipfile
from datetime import datetime
from pathlib import Path
from lxml import etree

DTBOOK = "http://www.daisy.org/z3986/2005/dtbook/"
OPF = "http://openebook.org/namespaces/oeb-package/1.0/"
DC = "http://purl.org/dc/elements/1.1/"
Q = lambda ns, name: f"{{{ns}}}{name}"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--project", type=Path, required=True); args = ap.parse_args()
    root = args.project.resolve()
    from project_data import ensure_pdf_project_layout
    ensure_pdf_project_layout(root)
    data = json.loads((root / "structure/structure.json").read_text(encoding="utf-8"))
    metadata = json.loads((root / "metadata/nimac.json").read_text(encoding="utf-8"))
    required=('title','publisher','identifier','language','source_isbns','subjects','publication_year','copyright_year','state_edition','content_type')
    missing_metadata=[key for key in required if not metadata.get(key) or (isinstance(metadata.get(key),list) and not any(metadata.get(key)))]
    if missing_metadata: raise SystemExit('Falta metadata NIMAC obligatoria: '+', '.join(missing_metadata))
    units = data.get("units", [])
    if not units: raise SystemExit("No hay unidades en la estructura del proyecto.")
    approved = json.loads((root / "revision/approvals.json").read_text(encoding="utf-8")) if (root / "revision/approvals.json").is_file() else {}
    missing = [u.get("id") for u in units if approved.get(u.get("id")) is not True]
    if missing: raise SystemExit("Faltan aprobaciones humanas: " + ", ".join(missing))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S"); out = root / "deliverables" / stamp; package = out / "nimas"
    package.mkdir(parents=True, exist_ok=True); images = package / "images"; images.mkdir()
    book = etree.Element(Q(DTBOOK, "dtbook"), nsmap={None: DTBOOK}); etree.SubElement(book, Q(DTBOOK, "head"))
    book_node = etree.SubElement(book, Q(DTBOOK, "book")); front = etree.SubElement(book_node, Q(DTBOOK, "frontmatter")); etree.SubElement(front, Q(DTBOOK, "doctitle")).text = str(metadata.get("title", root.name)); body = etree.SubElement(book_node, Q(DTBOOK, "bodymatter")); rear = etree.SubElement(book_node, Q(DTBOOK, "rearmatter"))
    for unit in units:
        source = root / "revision/approved" / f"{unit['id']}.xml"
        node = etree.fromstring(source.read_bytes())
        if etree.QName(node).namespace is None:
            for element in node.iter():
                element.tag = Q(DTBOOK, etree.QName(element).localname)
        target = front if unit.get("section") == "frontmatter" else rear if unit.get("section") == "rearmatter" else body
        target.append(node)
    xml_path = package / f"{root.name}.xml"; etree.ElementTree(book).write(str(xml_path), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    referenced = {node.get("src") for node in book.iter(Q(DTBOOK, "img")) if node.get("src")}
    candidates = {item.name: item for item in (root / "working/detected-images").rglob("*") if item.is_file()} if (root / "working/detected-images").is_dir() else {}
    for src in referenced:
        candidate = candidates.get(Path(src).name)
        if candidate:
            target = package / src
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, target)
    identifier=str(metadata.get('identifier') or root.name); opf_root = etree.Element(Q(OPF, "package"), version="1.0", **{"unique-identifier":"book-id"}, nsmap={None: OPF, "dc": DC}); metadata_node = etree.SubElement(opf_root, Q(OPF, "metadata"))
    def dc(name, value, **attrs):
        node=etree.SubElement(metadata_node,Q(DC,name),**attrs); node.text=str(value); return node
    dc('title', metadata.get('title', root.name))
    for key in ('creators','subjects'):
        values=metadata.get(key) or []; values=values if isinstance(values,list) else [values]
        for value in values:
            if key=='creators' and isinstance(value,dict):
                name=value.get('name'); role=value.get('role','author')
                if name: dc('creator',name,role=role)
            elif value: dc('creator' if key=='creators' else 'subject', value, **({'role':'author'} if key=='creators' else {}))
    if metadata.get('publisher'): dc('publisher',metadata['publisher'])
    dc('format','NIMAS 1.1')
    dc('rights',metadata.get('rights') or 'The only legal and authorized use of these files is for the production of alternate media materials for blind, visually impaired, or print disabled students as specified in the NIMAC limitation of use agreement. The copyright for these files is the sole property of the original owner.')
    dc('date',datetime.now().strftime('%Y-%m-%d'),event='DCTERMS.created')
    dc('identifier',identifier+'NIMAS' if not identifier.endswith('NIMAS') else identifier,id='book-id',scheme='NIMAS')
    if metadata.get('language'): dc('language',metadata['language'])
    for value in (metadata.get('source_isbns') or []):
        dc('source',value)
    for name,key in (('nimas-SourceDate','publication_year'),('DCTERMS.date.issued','publication_year'),('DCTERMS.date.dateCopyrighted','copyright_year'),('nimas-SourceEdition','edition'),('DCTERMS.format.extent','source_pagination'),('DCTERMS.description.version','state_edition'),('DCTERMS.description.note','content_type'),('DCTERMS.relation.isPartOf','series'),('DCTERMS.description.note','publisher_note')):
        if metadata.get(key): etree.SubElement(metadata_node,Q(OPF,'meta'),name=name,content=str(metadata[key]))
    for grade in (metadata.get('grade_levels') or []):
        etree.SubElement(metadata_node,Q(OPF,'meta'),name='DCTERMS.audience.educationLevel',content=str(grade))
    manifest = etree.SubElement(opf_root, Q(OPF, "manifest")); etree.SubElement(manifest, Q(OPF, "item"), id="dtbook", href=xml_path.name, **{"media-type":"application/x-dtbook+xml"})
    for image in sorted(package.joinpath("images").rglob("*")):
        if image.is_file():
            href=str(image.relative_to(package)).replace("\\","/")
            etree.SubElement(manifest, Q(OPF, "item"), id="img_"+image.stem, href=href, **{"media-type":"image/"+image.suffix[1:].lower()})
    spine = etree.SubElement(opf_root, Q(OPF, "spine")); etree.SubElement(spine, Q(OPF, "itemref"), idref="dtbook"); opf_path = package / f"{root.name}.opf"; etree.ElementTree(opf_root).write(str(opf_path), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    checks=[]; parsed=etree.parse(str(xml_path)); xml_root=parsed.getroot()
    if etree.QName(xml_root).localname != 'dtbook': checks.append('La raíz no es dtbook')
    refs={node.get('src') for node in parsed.xpath('//*[local-name()="img"]') if node.get('src')}
    missing=[src for src in refs if not (package/src).is_file()]
    if missing: checks.append('Imágenes inexistentes: '+', '.join(sorted(missing)[:5]))
    manifest_refs={node.get('href') for node in etree.parse(str(opf_path)).xpath('//*[local-name()="manifest"]/*[local-name()="item"]') if node.get('href')}
    if missing_manifest:=sorted(refs-manifest_refs): checks.append('Imágenes ausentes del OPF: '+', '.join(missing_manifest[:5]))
    dtd_path=Path(__file__).with_name('dtbook-2005-3.dtd')
    if dtd_path.is_file():
        dtd=etree.DTD(str(dtd_path))
        if not dtd.validate(parsed): checks.append('El DTBook no valida contra dtbook-2005-3.dtd: '+ '; '.join(str(e) for e in list(dtd.error_log)[:3]))
    if checks: raise SystemExit('Paquete no válido: '+ ' | '.join(checks))
    zip_path = out / f"{root.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for file in package.rglob("*"):
            if file.is_file(): z.write(file, file.relative_to(out))
    packaged_images=[p for p in package.joinpath("images").rglob("*") if p.is_file()]
    report = {"status":"pass", "package":str(package.relative_to(root)), "zip":str(zip_path.relative_to(root)), "units":len(units), "images":len(packaged_images), "imageCandidates":len(candidates), "unmatchedImageReferences":sorted(referenced - {str(p.relative_to(package)).replace("\\","/") for p in packaged_images})}
    (out / "validacion.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"); print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__": main()
