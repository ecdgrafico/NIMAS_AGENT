# Bitácora de corrección — FM a Lección 10

Estado: en proceso. Este documento registra sólo cambios ya aplicados al paquete de trabajo `9781669952961NIMAS`; el paquete `9781669952961NIMAS_original` permanece sin modificar.

| Alcance | Cambio aplicado | Razón | Evidencia / validación |
| --- | --- | --- | --- |
| XML de trabajo, Lección 2 | Se eliminaron un cierre `</list>` sin apertura, se cerró la lista de la actividad B de la página 18 y se cerraron correctamente la celda, fila y tabla de la actividad D de la página 36. | Los cierres cruzados impedían analizar o validar el libro completo como XML. No se cambió texto ni se reordenó contenido. | `xmllint --noout` termina correctamente. |
| FM | Se retiró la página final viii, que sólo contenía una imagen blanca heredada a 72 DPI. | El PDF la presenta en blanco y la política editorial indicada es no incluir páginas blancas finales ni imágenes ficticias. | Ya no existe referencia a `images/fm/0148689d_2.png`. |
| EM | Se retiraron los siete `imggroup` blancos heredados y sus `pagenum` 289–295. | El EM no tiene imágenes; esos PNG no existen en el paquete de trabajo, son blancos a 72 DPI en el paquete original y no corresponden a páginas con contenido editorial. | Ya no hay referencias `images/em/abd8ad87_*.png`. |
| Reglas de la habilidad | Se conserva `_` dentro de `span.WOL` cuando el PDF imprime una línea de respuesta y se omiten páginas finales en blanco. | Mantiene el respaldo visual solicitado sin convertir líneas de respuesta en texto añadido. | Regla actualizada en `nimas-semantic-review/SKILL.md`. |
| Lección 1, páginas 1–12 | Se integró la corrección semántica completa: una única `level1`/`h1`, temas en `level2`/`h2`, y actividades independientes en `level3`/`h3` con A., B., C., etc. Las cajas “Letters to Use” y “Words to Use” son `sidebar render="required"` con `hd` y lista. Se preservaron los subrayados de respuesta en `span.WOL`, los 64 recursos L01 de 300 DPI y su declaración OPF. | Las versiones previas abrían una `level1` por página y trataban instrucciones y actividades como encabezados de primer nivel. Eso impedía una navegación didáctica correcta y ocultaba la función de las cajas de apoyo. | XML bien formado; 64/64 referencias L01 resuelven físicamente y están declaradas en el OPF; no quedan referencias `images/u01/`. |

## Criterios para las lecciones 1–10

- Cada lección será una sola `level1` con su `h1`; los `pagenum` no abrirán lecciones nuevas.
- Los temas didácticos serán `level2`/`h2`; cada actividad A., B., C., etc. será `level3`/`h3` con la puntuación visible.
- Las cajas de palabras se convertirán en `sidebar` con `hd` y lista.
- Cada imagen nueva se verificará en 300 DPI, se ubicará conforme al PDF, se declarará con `alt=""` y tendrá entrada única en el OPF.
- No se creará texto nuevo. Las respuestas y ejemplos se conservarán con `span class="WOL"` conforme a lo impreso.

## Próxima revisión

La primera pasada semántica continúa en la Lección 1, que servirá como patrón contrastable antes de aplicarlo a las lecciones 2–10. Los hallazgos repetidos se añadirán aquí como requisitos de mejora para la aplicación de conversión.
