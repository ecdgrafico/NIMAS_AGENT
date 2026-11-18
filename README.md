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

## Ejecución en Windows PowerShell 5.1

Desde `C:\www\NIMAS_AGENT-1`, ejecute sólo una de estas líneas, sin pegar el texto de salida de la consola:

```powershell
.\run_agent.cmd -Book PHE27
```

O directamente:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_agent.ps1 -Book PHE27
```

La reconstrucción semántica XML/OPF es la prioridad. El proceso de imágenes es un módulo separado y puede terminar en revisión humana. El aprendizaje entre títulos se conserva como memoria explícita y versionada; no se aplican reglas nuevas globalmente sin evidencia.
