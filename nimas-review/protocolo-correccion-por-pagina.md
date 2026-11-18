# Protocolo obligatorio de corrección por página

Cada página se cierra sólo cuando la cola registra todos estos controles como verdaderos:

1. PDF revisado visualmente; no sólo por extracción de texto.
2. Texto y jerarquía XML corregidos conforme a la página y a su continuidad con la anterior.
3. Cada imagen extraída se ubicó contra el PDF, con `alt=""`, identificador único y sin imagen heredada.
4. La entrada OPF coincide con los recursos XML de la página.
5. XML bien formado después de la edición.

Estados permitidos:

- `pending`: sin revisión editorial.
- `in_progress`: PDF abierto y edición activa.
- `complete`: los cinco controles anteriores se verificaron.
- `blocked`: falta una fuente editorial o existe una ambigüedad que no puede resolverse desde el PDF.

No se permite marcar una lección completa por conteo de imágenes ni por una transformación global. La unidad de cierre es cada página editorial; las secciones y actividades que cruzan página permanecen en el mismo nivel XML.
