# Auditoría del paquete corregido

Fecha: 2026-11-17. Paquete auditado: `9781669952961NIMAS_corregido/`.

## Resultado técnico

- El DTBook contiene 24 `level1` consecutivos: `Lesson 1` a `Lesson 24`.
- Las actividades de letra se normalizaron como `level3` con `h3` que comienza por `A.`, `B.`, etc., bajo el tema pertinente (`level2`).
- Los títulos que habían quedado arrastrados a la lección siguiente fueron reasignados a su `level1` correspondiente.
- Las cajas textuales `Letters to Use` y `Words to Use` que se identificaron como párrafos se convirtieron en `sidebar render="required"`, con encabezado y lista.
- Cada una de las 996 imágenes PNG del paquete aparece una sola vez en el XML y está declarada en el OPF.
- No hay rutas de imágenes faltantes ni recursos de imagen sin usar.
- No permanecen referencias al conjunto heredado `images/uXX` de 72 DPI. La ruta `images/FM/...` es la nueva imagen FM a 300 DPI, no un recurso heredado.
- `alt` está declarado vacío en las imágenes, conforme a la decisión editorial.
- XML y OPF están bien formados con `xmllint --noout`.
- El XML y el OPF no contienen tabulaciones ni sangría inicial; los saltos de línea se conservan.

## Alcance editorial incorporado

- FM, Lessons 1–24 y EM se preservan en el paquete.
- Las páginas finales en blanco de FM/EM no se incorporan como contenido ni como recursos de imagen.
- EM no recibe imágenes, por decisión editorial.
- El paquete original no fue alterado; el resultado se encuentra exclusivamente en la carpeta `9781669952961NIMAS_corregido/`.

## Límite de la comprobación

El CSV del validador NIMAS recibido después de la primera entrega reportó 178 incidencias. Se corrigieron las clases mecánicas reportadas: `imggroup` vacíos, niveles sin encabezado/contenido, anidamiento directo de niveles iguales, `caption/@imgref` con rutas en vez de IDREF y archivos `.DS_Store` dentro del conjunto. El ZIP de entrega excluye explícitamente `.DS_Store`.

La validación contra DTD no se puede repetir localmente porque el entorno no tiene disponible la DTD DTBook requerida ni acceso a su URL pública. El siguiente control debe ejecutarse con el mismo validador NIMAS que produjo el CSV sobre el ZIP actualizado.
