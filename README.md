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

En el primer inicio pedirá la ruta de `PHE27_NIMAS`, creará `.venv` e instalará automáticamente las dependencias de Python. La ruta queda sólo en `config/project.local.json`, que no se sube a Git. Después abrirá `http://127.0.0.1:8000/auditoria-lecciones/`.

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

## Auditoría editorial local

`auditoria-lecciones/` añade una mesa de revisión por página: PDF, XML fuente,
propuesta del agente, recursos asociados y navegación anterior/siguiente. No
publica ni instala una propuesta automáticamente. Consulte
`docs/arquitectura-y-migracion.md` y ejecute `iniciar_auditoria.ps1` en Windows
para el flujo local portable.
