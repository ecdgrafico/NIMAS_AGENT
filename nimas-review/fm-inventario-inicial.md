# Inventario inicial: Frontmatter (FM)

Estado: diagnóstico; no se modifica XML, OPF ni recursos.

## Fuente editorial

- PDF: `PDF/PHE27_SE_FM_i-iv_hi.pdf`.
- El nombre del archivo dice `i-iv`, pero el PDF contiene 8 páginas: i–viii.
- Páginas i–vii: portada, créditos y contenido. Página viii: página en blanco de producción; no contiene contenido editorial ni imagen sustantiva.

## Recursos de imagen

| Recurso | XML/OPF | Archivo físico | DPI | Dictamen |
| --- | --- | --- | --- | --- |
| `images/fm/0148689d_2.png` | Original: referenciado en XML y OPF para la página viii | Presente solo en el paquete original | 72 × 72 | Recurso heredado de baja resolución; además la página viii del PDF está en blanco. No debe migrarse sin aprobación. |
| `images/FM/PHE27_SE_FM_pi_01.png` | Paquete de trabajo: referenciado en XML y OPF para la página i | Presente | 300 × 300 | Recurso extraído disponible. PNG RGBA con transparencia; corresponde al logotipo de portada. |

Existe la carpeta `images/FM` y contiene **1** PNG extraído de FM a 300 DPI, disponible para incorporar.

## Hallazgos XML

1. El paquete original no contiene imagen en la página i, aunque el PDF muestra el logotipo Vista Higher Learning como elemento gráfico además del texto.
2. El paquete de trabajo añade una referencia para una imagen de página i; el archivo está presente y su ID y ruta coinciden con XML y OPF.
3. El único recurso FM original es una imagen blanca asociada con página viii, a 72 DPI. El PDF confirma que la página viii está en blanco, por lo que esta imagen parece un artefacto de conversión, no contenido editorial que requiera reemplazo a 300 DPI.

## Próxima propuesta, pendiente de aprobación

- No retener la imagen blanca heredada de página viii.
- Conservar el logotipo de portada extraído a 300 DPI en `images/FM/`, con la ruta e ID ya coherentes en XML y OPF.
