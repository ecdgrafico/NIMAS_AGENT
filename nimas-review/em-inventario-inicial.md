# Inventario inicial — EM / rearmatter

## Alcance revisado

Fuente editorial: `PDF/PHE27_SE_EM_287-304_hi.pdf`.

El PDF tiene 18 páginas físicas y sus folios impresos son 287–304. Las páginas 287–297 contienen contenido editorial: créditos fotográficos y artísticos, seguido por el índice de destrezas. Las páginas 298–304 son páginas de producción en blanco; la página 298 sólo muestra su folio en el pie. La comprobación se hizo también por renderizado visual, no sólo por extracción de texto.

## Recursos gráficos

| Ubicación | Estado | Resolución |
| --- | --- | --- |
| `9781669952961NIMAS/images/EM/` o `images/em/` | No existe: no hay imágenes EM extraídas en el paquete de trabajo. | — |
| `9781669952961NIMAS_original/images/em/abd8ad87_{7,8,9,10,11,12,14}.png` | Existen 7 imágenes heredadas. Son páginas blancas rasterizadas, sin contenido editorial. | 2782 × 3382 px, 72 DPI |

No falta una imagen editorial de 300 DPI: las siete páginas a las que alude el XML son blancas en el PDF. Por tanto no corresponde fabricar sustitutos de 300 DPI ni conservar los PNG heredados de 72 DPI sólo para representar hojas vacías.

## Hallazgos de integridad

1. El XML de trabajo aún referencia los siete PNG heredados (`images/em/abd8ad87_*.png`) en las líneas 13108–13132, pero no existen físicamente. Esas referencias hacen que el paquete sea inconsistente.
2. El OPF de trabajo no declara los siete recursos. El OPF original sí los declara (líneas 642–648), pero sus archivos son de 72 DPI y no deben migrarse.
3. Las referencias heredadas están vinculadas a los folios 289–295, mientras que el PDF muestra que las páginas blancas reales son 298–304. Es un desfase de nueve folios y evidencia que no deben reutilizarse como guía de paginación.
4. El contenido textual visible de 287–297 debe mantenerse como XML semántico —no como imagen— y contrastarse con el PDF durante la corrección final. No se incorporará texto inventado.

## Propuesta para aprobación

- Corregir la secuencia de `pagenum` de EM contra los folios del PDF, preservando el contenido de créditos e índice de 287–297 con estructura DTBook apropiada.
- Eliminar del XML las siete referencias a imágenes blancas, sus `imggroup` y, si se incorporaran por accidente, sus siete entradas de manifiesto OPF. No añadir imágenes de sustitución para 298–304.
- Conservar los `pagenum` 298–304 si se requiere representar la paginación completa, pero sin imágenes ficticias ni contenido añadido.
- Registrar explícitamente en el informe final que EM no requiere recursos de imagen de 300 DPI. Si se suministran imágenes con contenido para EM en el futuro, deberán ubicarse en `images/EM/`, verificarse a 300 DPI, declararse en el OPF y mapearse contra el PDF antes de referenciarlas.

## Límite de esta fuente

Este PDF comienza en el folio 287. El `rearmatter` del XML contiene material anterior; se revisará con el PDF que cubra sus folios correspondientes, no se inferirá desde esta fuente.
