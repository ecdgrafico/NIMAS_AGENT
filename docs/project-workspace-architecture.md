# Arquitectura de navegación de proyectos

NIMAS Agent sigue el patrón de aplicaciones de escritorio como VS Code y GitHub
Desktop: una biblioteca independiente y un espacio de trabajo con un proyecto
activo. La biblioteca nunca conserva unidades de un proyecto anterior.

## Estados

- `library`: no hay proyecto activo; muestra proyectos y creación/importación.
- `opening`: se bloquean las acciones mientras se valida y abre el proyecto.
- `workspace`: existe un proyecto activo; todas las vistas consultan su API.
- `closing`: al volver a Biblioteca se cierra primero el proyecto anterior.

## Transiciones

```text
Biblioteca --Abrir--> Apertura --> Espacio de trabajo
Espacio de trabajo --Proyectos--> Cierre --> Biblioteca
Biblioteca --Abrir otro--> Apertura --> Espacio de trabajo nuevo
```

La transición de cierre es explícita mediante `/api/close-project`; esto evita
que una respuesta tardía de una apertura anterior contamine el siguiente
proyecto. La interfaz oculta los controles de Biblioteca hasta que termina el
cierre.

Este patrón sigue el modelo documentado de workspaces: el nombre y el contexto
actual se muestran en el espacio de trabajo, mientras que la lista de proyectos
permanece como selector independiente.
