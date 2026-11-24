# Verificación de un título real

Esta lista se ejecuta después de crear o abrir un proyecto. No modifica PDFs ni
el ZIP original.

## Ingreso y estructura

- [ ] El proyecto aparece en la biblioteca.
- [ ] Todos los PDFs de referencia están en `fuentes/pdf`.
- [ ] Cada unidad tiene nombre, PDF, rango de páginas y sección editorial.
- [ ] FM, bodymatter y EM fueron revisados por una persona.
- [ ] Si existe una unidad patrón, está marcada como referencia.

## Propuesta DTBook

- [ ] Se completó `metadata/nimac.json` con los datos del título.
- [ ] Se ejecutó el análisis de imágenes.
- [ ] Cada imagen fue asignada a una unidad o descartada con justificación.
- [ ] La propuesta contiene todas las páginas del rango PDF.
- [ ] Se revisaron jerarquía, listas, tablas, captions, texto y páginas en blanco.
- [ ] Se revisó cualquier archivo `versions/ai-runs/*-fallback.md`.
- [ ] La propuesta pasó la validación XML/DTBook.
- [ ] La persona responsable la aprobó desde la aplicación.

## Paquete entregable

- [ ] El preflight devuelve `pass`.
- [ ] El exportador genera DTBook, OPF, manifiesto y spine.
- [ ] Las imágenes referenciadas existen y no quedan referencias huérfanas.
- [ ] El ZIP abre correctamente y conserva la estructura NIMAS esperada.
- [ ] El ZIP fue revisado con la herramienta oficial de validación/subida de NIMAC.
- [ ] El ZIP final y el informe de preflight se guardaron en el entregable del proyecto.

## Evidencia mínima

Conservar `inventario/project.json`, `inventario/images.json`,
`metadata/nimac.json`, `structure/structure.json`, `revision/approvals.json`,
el informe de validación de cada unidad y el informe final de preflight junto al
ZIP entregable.
