# Estado de implementación

## Cubierto y verificado

- Biblioteca local de proyectos PDF-first y ZIP-first.
- Conservación no destructiva del ZIP original.
- Inventario de PDF, XML, OPF y recursos.
- Clasificación inicial FM, bodymatter y EM.
- Edición de unidades, orden y rangos dentro de un PDF combinado.
- Carga incremental de PDF en un proyecto ya creado, con inventario y unidades nuevas.
- Extracción de imágenes del PDF y decisiones humanas de asociación.
- Metadata NIMAC y mapeo al OPF.
- Generación revisable de cover, title page y copyright.
- Propuestas mediante Codex u Ollama local.
- Validación fail-closed de XML, aprobaciones, imágenes y metadata.
- Exportación de DTBook, OPF y ZIP.
- Pruebas automatizadas: ejecutar python -m unittest discover -s tests -v.

## Revisión humana obligatoria

- La IA no instala propuestas automáticamente.
- Las imágenes no se asocian al XML solo por nombre o posición; deben cotejarse
  con el PDF y aprobarse.
- El contenido semántico generado por un modelo local puede ser incompleto y se
  rechaza si no pasa el validador.
- El ZIP solo es entregable después de completar preflight y aprobación humana.

## Pendiente para declarar producción completa

- Validación con títulos reales adicionales y sus variaciones editoriales.
- Revisión visual de cada página e imagen del primer proyecto nuevo.
- Confirmación final del ZIP con la herramienta de validación/subida de NIMAC.
