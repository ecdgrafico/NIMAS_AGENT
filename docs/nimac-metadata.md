# NIMAC metadata aplicada

Fuente normativa: [NIMAC Metadata Guidelines](https://nimac.us/nimac-metadata-guidelines/).

El formulario guarda los datos en metadata/nimac.json. El exportador los
transforma al OPF:

| Campo del proyecto | OPF |
| --- | --- |
| title | dc:Title |
| creators | dc:Creator role="author" por defecto |
| publisher | dc:Publisher |
| identifier | dc:Identifier scheme="NIMAS" + sufijo NIMAS |
| language | dc:Language |
| source_isbns | dc:Source repetible |
| subjects | dc:Subject repetible |
| publication_year | nimas-SourceDate y DCTERMS.date.issued |
| copyright_year | DCTERMS.date.dateCopyrighted |
| edition | nimas-SourceEdition |
| state_edition | DCTERMS.description.version |
| content_type | DCTERMS.description.note |
| series | DCTERMS.relation.isPartOf |
| grade_levels | DCTERMS.audience.educationLevel repetible |
| source_pagination | DCTERMS.format.extent |
| rights | dc:Rights, con el texto predeterminado si está vacío |
| publisher_note | DCTERMS.description.note adicional |

El preflight bloquea la exportación si falta un campo requerido, una unidad no
está aprobada o su XML aprobado no existe/no es XML bien formado.
