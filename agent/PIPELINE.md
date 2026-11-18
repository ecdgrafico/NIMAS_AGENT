# Pipeline de reconstrucción

## A. XML y OPF primero

- Preservar el paquete original.
- Inventariar referencias XML/OPF a imágenes inválidas.
- Eliminar referencias y entradas de manifiesto que no tengan recurso válido.
- Reconstruir cada lección completa usando el PDF como autoridad de orden y límites.
- Mantener texto visible y no inventar contenido.
- Validar XML bien formado, DTD y consistencia OPF después de cada unidad.

## B. Imágenes después

- Crear inventario de imágenes disponibles y sus dimensiones/DPI.
- Proponer coincidencias limitadas por página y contenido visual.
- Aplicar sólo coincidencias de confianza suficiente.
- Enviar las ambiguas a revisión humana.
- No conservar imágenes inválidas sólo para satisfacer referencias heredadas.

## C. Publicación

El ZIP sólo se genera cuando XML, OPF, recursos, paginación y validaciones están en estado `pass`. Un paquete con imágenes pendientes se entrega como revisión, nunca como paquete final.
