# NIMAS Agent — PHE27

Agente PDF-led para reconstruir y validar paquetes NIMAS/DTBook, XML y OPF.

## Estructura de trabajo

- `agent/`: reglas y documentación reutilizable del agente.
- `nimas-agent/`: scripts técnicos heredados y validadores del proyecto.
- `nimas-semantic-review/`: habilidad de revisión semántica PDF → DTBook.
- `PDF/`: fuentes editoriales; no modificar.
- `images/`: recursos extraídos de alta resolución; no modificar.
- `nimas-review/`: mapas, propuestas y reportes de revisión.
- `work/`: paquetes reconstruidos en proceso.
- `deliverables/`: ZIPs finales aprobados.
- `evidence/`: inventarios, hashes, logs y resultados de validación.

## Flujo obligatorio

Inventario → mapa por página → calibración semántica → revisión → corrección controlada → auditoría fail-closed → validación DTD/NIMAS → empaquetado.

El ZIP `9781669952961NIMAS_original.zip` es la fuente y debe permanecer intacto.
