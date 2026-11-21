# Gestor local de auditoría NIMAS

El gestor descubre las lecciones originales del proyecto, muestra su estado y
permite generar propuestas pendientes desde la cola. No modifica el paquete
NIMAS: la aprobación es editorial y se guarda en el navegador hasta que se
instale explícitamente una lección aprobada.

Desde la raíz del proyecto, iniciar:

```sh
python3 nimas-agent/servidor_auditoria.py
```

Luego abrir `http://localhost:8000/auditoria-lecciones/`.

## Generar propuestas

En la interfaz, usa **Generar esta lección** o **Generar pendientes**. La cola
se ejecuta secuencialmente para que cada propuesta pueda validar sus imágenes
y su estructura antes de continuar. También se puede usar la terminal:

```sh
./nimas-agent/generar_propuesta_leccion.sh 6
python3 nimas-agent/validar_propuesta_leccion.py 6
```

El primer comando inicia el agente para crear la propuesta **completa** de L04
como fragmento `level1` (sin envoltura DTBook repetida).
Al terminar, recarga el navegador: el auditor detectará
`lecciones_propuestas/L04.xml` y mostrará la propuesta por página. El agente
no instala cambios en el paquete; la aprobación continúa siendo editorial. Si
el agente solicita autorización para escribir la propuesta, revísala y aprueba
sólo las acciones dentro de `lecciones_propuestas/` y `nimas-review/agent-runs/`.

La vista combina un render de la página del PDF, el fragmento del XML original,
la propuesta generada por el agente y los cinco controles obligatorios. La
aprobación se habilita sólo cuando todos los controles de la página están
marcados.

## Nuevo proyecto

Crear un proyecto aislado a partir de tres carpetas (paquete original, paquete
con progreso manual y PDF):

```sh
python3 nimas-agent/inicializar_proyecto_nimas.py \
  --original "/ruta/paquete-original" \
  --progreso "/ruta/paquete-con-progreso" \
  --pdf "/ruta/PDF" \
  --destino "/ruta/Nuevo_proyecto_NIMAS"
```

El destino debe ser nuevo o estar vacío. El inicializador copia las fuentes,
separa los fragmentos y deja el nuevo proyecto listo para iniciar con el mismo
servidor local.
