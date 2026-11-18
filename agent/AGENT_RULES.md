# Reglas del agente NIMAS

1. No modificar el ZIP original, los PDFs ni las imágenes fuente.
2. Usar el PDF editorial como autoridad de orden visual, paginación y límites de contenido.
3. Crear o actualizar un mapa por página antes de editar XML.
4. No inventar, corregir ni completar texto que no esté sustentado por el PDF o la fuente XML.
5. Mantener `alt=""` salvo que exista una política de accesibilidad explícita.
6. Cada imagen referenciada debe existir físicamente y tener una entrada única en el OPF.
7. Cada corrección material exige auditoría posterior.
8. No publicar si hay anclas faltantes, orden de páginas inconsistente, errores DTD/NIMAS, recursos faltantes o revisión pendiente.
9. El paquete final sólo se crea mediante `package_if_valid.py` después de un resultado `pass`.
10. Registrar comandos, entradas, salidas, hashes y bloqueos en `evidence/`.
