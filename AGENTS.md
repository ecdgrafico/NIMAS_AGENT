# Contexto operativo para agentes de IA

## Objetivo

Este repositorio contiene la aplicación local para remediar y auditar paquetes NIMAS/DTBook. La autoridad editorial es el PDF. El XML fuente ayuda a recuperar texto y recursos, pero puede tener contenido, estructura o paginación erróneos.

El usuario revisa visualmente y aprueba; el agente propone cambios y nunca debe instalar una propuesta directamente en el paquete fuente.

## Reglas no negociables

1. No modificar el ZIP original, los PDF, las imágenes fuente ni un paquete NIMAS fuente.
2. No inventar texto ni descripciones: todo cambio debe sustentarse en el PDF o XML fuente.
3. Una lección es un fragmento con un único `level1`; las páginas son `pagenum`, no documentos ni `level1` separados.
4. FM y EM son unidades auditables. Si XML y PDF difieren, crear propuesta de reconstrucción desde PDF.
5. Asociar imágenes al ítem, ejemplo o lectura correspondiente. Omitir decoración justificada; nunca dejar imágenes huérfanas en el ZIP/OPF.
6. Validar XML, DTD DTBook, recursos XML–OPF y ZIP antes de exportar.
7. El PDF es la referencia para rangos, jerarquía de títulos, orden visual y contenido existente.

## Flujo de trabajo

1. Abrir la auditoría con `NIMASAPP` en Windows o `python3 nimas-agent/servidor_auditoria.py` en macOS.
2. Comparar PDF, XML fuente y propuesta por página.
3. Corregir por página cuando exista una solicitud editorial; no regenerar una lección completa innecesariamente.
4. Aprobar lección/FM/EM sólo tras la revisión humana.
5. Usar **Crear ZIP validado** para generar un resultado nuevo, fechado y no destructivo.

## Contexto actual de PHE27

- Lecciones 1–3 son patrones humanos de referencia.
- El trabajo final requiere estructura semántica para tablas, listas, WOL, sidebars, ejemplos, Decodable Readers e imágenes inline.
- Algunos XML heredados tienen rangos erróneos; el tramo final y el rear matter requieren recuperación PDF-led.
- El exportador debe dejar XML y OPF sin sangría inicial, con un `<item>` por línea en el manifiesto OPF.

## Pruebas con Ollama

Ollama puede usarse para generar propuestas o analizar diferencias, pero no para aprobar ni exportar automáticamente. Cualquier integración debe quedar detrás de un proveedor explícito y conservar: PDF + XML fuente + reglas editoriales + solicitud por página. La salida de un modelo local siempre pasa por la misma validación y auditoría humana.
