## Ejecución local

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Dependencias mínimas: `lxml`, `pypdf`, `Pillow`.

Los scripts actuales contienen rutas históricas y algunas transformaciones específicas de lección. El agente debe convertirlas gradualmente en comandos parametrizados antes de usarlas para otro libro.
