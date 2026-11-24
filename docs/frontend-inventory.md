# Inventario del frontend Vue

## Vistas

- `ProjectLibraryView.vue`: biblioteca, creación y apertura de proyectos.
- `ProjectWorkspaceView.vue`: resumen del proyecto activo y navegación por etapas.
- `LessonAuditView.vue`: selección de unidad, generación y validación de propuestas DTBook.
- `MetadataView.vue`: formulario inicial de metadata NIMAC conectado a `/api/nimac-template`.
- `StructureView.vue`: clasificación final de unidades en Frontmatter, Bodymatter y Rearmatter.

## Componentes

- `AppShell.vue`: encabezado y navegación global.
- `ProjectList.vue`: listado de proyectos de `/api/projects`.
- `ProjectCreateForm.vue`: carga PDF o ZIP mediante FormData.

## Composables

- `useProjects.js`: carga y creación de proyectos.
- `useProject.js`: carga de estado y detalle del proyecto activo.

## Servicios

- `services/api.js`: cliente centralizado para las APIs Python; concentra errores y `no-store`.

## Rutas

| Ruta | Vista |
|---|---|
| `/projects` | Biblioteca |
| `/workspace` | Proyecto activo |
| `/lessons` | Generación y validación DTBook |
| `/metadata` | Metadata NIMAC |
| `/structure` | Ensamblaje final |

La migración mantiene `auditoria-lecciones/` como frontend legacy hasta completar la paridad funcional.
