# Arquitectura y migración a Windows

## Principio operativo

La aplicación se ejecuta localmente junto a los archivos editoriales. GitHub
guarda el código; los libros y sus recursos permanecen en un disco controlado.
El servidor usa `127.0.0.1` por defecto.

## Capas

1. **Datos editoriales locales:** PDF, XML, imágenes, propuestas y aprobaciones.
2. **Motor determinista:** separación, validación DTBook, rangos, recursos e informes.
3. **Adaptador de agente:** genera propuestas y registra etapas y resultados.
4. **Auditoría humana:** cotejo visual con PDF y aprobación de la unidad completa.

## UX objetivo: mesa de edición

La auditoría necesita navegación persistente:

```text
[ anterior ]  Página X de Y  [ siguiente ]
rail | XML fuente | PDF | propuesta
imágenes asociadas: panel plegable
```

Al cambiar de página se actualizan juntos PDF, fuente, propuesta e imágenes;
no debe ser necesario volver al encabezado.

## Ruta de migración

1. Terminar la navegación persistente y el panel de progreso.
2. Inicializar Git en esta carpeta o copiar el código a tu repositorio GitHub.
3. Confirmar que `.gitignore` mantiene el contenido editorial fuera del repositorio.
4. Crear una versión `v0.1.0` y clonarla en Windows.
5. Copiar localmente un proyecto de prueba y ejecutar los validadores.
6. Configurar Codex CLI o una API solo si se requieren propuestas nuevas.
7. Para acceso remoto, usar una VPN privada como Tailscale; no exponer el puerto
   de auditoría directamente a Internet.

## Pendientes de producto

- Barra pegajosa anterior/siguiente y atajos de teclado.
- Historial y comparación de versiones de propuesta.
- Aprobación de FM/EM y exportación final del paquete.
- Adaptador de agente Python multiplataforma con registro persistente.
- Pruebas automatizadas de rangos y fragmentos DTBook.
