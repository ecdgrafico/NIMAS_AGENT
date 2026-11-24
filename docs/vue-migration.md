# Migración del frontend a Vue

El frontend nuevo vive en `frontend-vue/` y coexiste con `auditoria-lecciones/` mientras se migran las pantallas.

## Desarrollo

```powershell
cd C:\www\NIMAS_AGENT-1\frontend-vue
npm install
npm run dev
```

El servidor Vite redirige `/api`, `/working` y `/auditoria-lecciones` al servidor Python en `127.0.0.1:8000`.

## Producción

```powershell
npm run build
```

El resultado queda en `frontend-vue/dist/`. La siguiente fase será hacer que `servidor_auditoria.py` pueda servir ese directorio mediante una opción de producción, manteniendo las APIs y el frontend legacy como respaldo durante la migración.

## Regla de migración

No se elimina una pantalla legacy hasta que la pantalla Vue equivalente tenga sus pruebas, sus llamadas API verificadas y una ruta de retorno al flujo anterior.
