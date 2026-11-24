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

## Inicio simple en Windows

1. Mantén este repositorio separado de la carpeta editorial `PHE27_NIMAS` (PDF, fuentes XML e imágenes). No copies esos materiales al repositorio.
2. En PowerShell, desde la carpeta del repositorio, ejecuta una sola vez:

```powershell
.\instalar_comando_nimasapp.ps1
```

3. Cierra y abre de nuevo la terminal integrada de VS Code. A partir de entonces escribe:

```powershell
NIMASAPP
```

Durante el desarrollo, para que los cambios de código se recarguen sin cerrar
la terminal, usa:

```powershell
NIMASAPP -Watch
NIMASAPP -Check  # diagnostica dependencias, pruebas y proveedores sin iniciar el servidor
```

La ventana queda limpia por defecto. Para diagnosticar solicitudes HTTP usa:

```powershell
NIMASAPP -Watch -DetailedLogs
```

WAMP no es necesario: la aplicación usa Python para el servidor local y
SQLite para la biblioteca de proyectos.

El primer inicio no carga ni solicita PHE27 ni ningún proyecto anterior: crea `.venv`, instala automáticamente las dependencias de Python y abre la landing vacía. El proyecto nuevo debe importarse desde esa landing. Para abrir de manera excepcional un proyecto local ya preparado, usa `NIMASAPP -ProjectRoot 'C:\ruta\Mi_proyecto_NIMAS'`.

Si prefieres no instalar el comando permanente, desde CMD puedes ejecutar `NIMASAPP.cmd`; desde PowerShell usa `.\NIMASAPP.cmd`.

Para ver las páginas PDF dentro de la app también necesitas Poppler (`pdftoppm`) disponible en `PATH`. La aplicación avisará claramente si no lo encuentra.

El archivo [AGENTS.md](AGENTS.md) contiene el contexto y las reglas que debe seguir Codex, Copilot u otra IA. Las pruebas con Ollama deben generar propuestas auditables, nunca aprobar o exportar de forma automática.

## Ejecución técnica anterior en Windows PowerShell 5.1

Desde `C:\www\NIMAS_AGENT-1`, ejecute sólo una de estas líneas, sin pegar el texto de salida de la consola:

```powershell
.\run_agent.cmd -Book PHE27
```

O directamente:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_agent.ps1 -Book PHE27
```

La reconstrucción semántica XML/OPF es la prioridad. El proceso de imágenes es un módulo separado y puede terminar en revisión humana. El aprendizaje entre títulos se conserva como memoria explícita y versionada; no se aplican reglas nuevas globalmente sin evidencia.

## Flujo PDF-first

1. Crear el proyecto cargando uno o varios PDF desde la aplicación. Los archivos originales se copian a la biblioteca local y nunca se modifican.
2. Revisar la estructura propuesta: `frontmatter`, `bodymatter`, `rearmatter` o `unclassified`. La detección inicial usa nombres como `FM`, `EM`, `L01`, `U01`, `PL`, `IU` y `UI`, pero la decisión final es humana.
3. Completar y guardar `metadata/nimac.json` y la estructura editorial.
4. Ejecutar el inventario visual. Las imágenes extraídas quedan en `working/detected-images` y no entran automáticamente al paquete.
5. Preparar y generar una propuesta XML por unidad. La propuesta se guarda en `propuestas/` y se valida estructuralmente.
6. Aprobar manualmente cada propuesta. Solo entonces se copia a `revision/approved/` y se registra en `revision/approvals.json`.
7. Crear el ZIP validado. El exportador PDF-led genera DTBook, OPF, manifiesto, spine y solo incorpora imágenes referenciadas por XML aprobado.

### Propuestas con Ollama local

La app detecta Ollama instalado en Windows y comprueba que el servicio responda con
ollama list. El proveedor local usa llama3.2 por defecto, por lo que no requiere
una API de pago.

```powershell
ollama list
$env:NIMAS_OLLAMA_MODEL = "llama3.2"
.\\NIMASAPP.cmd
```

La respuesta del modelo nunca se instala directamente: debe producir un fragmento
level1, pasar el validador y recibir aprobación humana antes de exportar el ZIP.

La exportación se bloquea si faltan unidades clasificadas/aprobadas o si existen referencias de imagen sin resolver. El exportador heredado de PHE27 permanece separado para no alterar su flujo aprobado.

## Iniciar un proyecto desde PDF

La app también puede iniciar un proyecto sin XML, OPF ni lecciones de ejemplo.
El primer paso crea una copia no destructiva de los PDF y un inventario de
páginas y texto:

```powershell
python nimas-agent/create_pdf_project.py `
  --pdf 'C:\ruta\a\los\PDF' `
  --destino 'C:\ruta\a\Mi_proyecto_NIMAS' `
  --nombre 'Mi libro'
```

El inventario queda en `inventario/project.json`. La siguiente etapa será la
extracción visual de imágenes y la generación de una propuesta DTBook/OPF por
un proveedor de IA, siempre como propuesta pendiente de auditoría.

## Auditoría editorial local

`auditoria-lecciones/` añade una mesa de revisión por página: PDF, XML fuente,
propuesta del agente, recursos asociados y navegación anterior/siguiente. No
publica ni instala una propuesta automáticamente. Consulte
`docs/arquitectura-y-migracion.md` y ejecute `iniciar_auditoria.ps1` en Windows
para el flujo local portable.
