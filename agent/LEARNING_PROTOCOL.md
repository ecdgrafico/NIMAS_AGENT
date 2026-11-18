# Protocolo de aprendizaje por título

El agente no modifica sus reglas generales de forma silenciosa. Cada título nuevo se analiza en fases y produce una memoria explícita que puede revisarse, aprobarse y reutilizarse.

## Fases

1. **Descubrimiento**: inventario de XML, OPF, PDFs, imágenes, paginación, namespaces y patrones de conversión.
2. **Calibración**: selección de una lección representativa y construcción de un mapa PDF → XML.
3. **Inferencia de reglas**: identificación de patrones de lecciones, secciones, actividades, tablas, listas, respuestas e imágenes.
4. **Prueba**: aplicación sólo a una segunda unidad y comparación estructural/visual.
5. **Generalización**: convertir únicamente los patrones repetidos y confirmados en reglas del título.
6. **Excepciones**: registrar las unidades que no siguen el patrón; nunca forzarlas mediante una transformación global.
7. **Memoria**: conservar reglas, decisiones, ejemplos, excepciones, confianza y evidencia de validación.

## Memoria separada

- Reglas generales: `agent/AGENT_RULES.md`.
- Reglas semánticas: `nimas-semantic-review/SKILL.md`.
- Reglas específicas del título: `work/<titulo>/title-rules.yaml`.
- Mapa y decisiones: `work/<titulo>/maps/` y `work/<titulo>/decisions/`.
- Revisión humana: `work/<titulo>/review-queue/`.
- Resultados aprobados: `deliverables/<titulo>/`.

Una regla nueva debe indicar origen, ejemplo, confianza, alcance y prueba que la respalda. Una decisión editorial de un libro no se convierte automáticamente en regla universal.
