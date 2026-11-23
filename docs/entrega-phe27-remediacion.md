# Entrega técnica y editorial · Remediación NIMAS PHE27

## Estado de entrega

Se completó la auditoría editorial de las unidades aprobadas, se ensambló un paquete NIMAS nuevo y se validó técnicamente antes de su envío a NIMAC. La aprobación de NIMAC sigue siendo la validación externa definitiva.

El resultado no debe entenderse como una conversión mecánica de XML: fue una remediación editorial cotejada contra el PDF, el XML fuente y los patrones manualmente remediados de las lecciones 1–3.

## Cambios fundamentales

### 1. La autoridad editorial es el PDF, no únicamente el XML heredado

- El XML fuente tiene pérdidas de estructura, contenido unido y rangos de página incorrectos en algunas unidades.
- La app debe comparar PDF, XML fuente y propuesta, y señalar cuando el rango o el contenido del XML no coincide con el PDF.
- Cuando hay una discrepancia, debe crear una **propuesta de recuperación desde PDF**, no propagar el error de la fuente.
- Este flujo fue necesario especialmente en el tramo final de lecciones 21–24 y para el rear matter. El rear matter fuente tenía un desfase de folios y contenido fuera del rango visual del PDF.

### 2. Las lecciones no son DTBooks independientes

- Los archivos de trabajo por lección son **fragmentos**, sin declaración XML, DOCTYPE, `<dtbook>`, `<head>`, `<book>`, `<bodymatter>` ni `<rearmatter>` repetidos.
- Un único `<level1>` abarca toda una lección: abre en su primera página y cierra únicamente en la última.
- Las páginas son anclas `<pagenum>` dentro de esa estructura; no son documentos ni `level1` independientes.
- Al mostrar una página en la interfaz se debe advertir que es un recorte de auditoría y que puede depender de niveles abiertos/cerrados en otra página. Para copiar o exportar se usa siempre el XML completo de la lección.

### 3. Se reemplazó la lectura lineal por estructura semántica

El contenido visual se convirtió según su función, no según su posición de extracción:

- Encabezados: `h1`, `h2` y `h3` con niveles DTBook coherentes.
- Tablas sólo cuando existe una relación real de filas y columnas; por ejemplo, patrones de sonido, clasificación y tablas de escritura.
- Ejercicios, opciones y correspondencias como `<list>` y `<li>`, con listas paralelas separadas cuando el PDF muestra columnas como `1–5` y `a–e`.
- Sidebars de “Words to Use” antes del ejercicio al que sirven, no mezclados con el flujo principal.
- Ejemplos separados del ejercicio y de sus imágenes; no se usa `<div class="example">`.
- Decodable Readers como una secuencia de ítems con la información de palabras decodificables y frecuencia alta estructurada, evitando párrafos o imágenes agrupadas sin relación.

### 4. Reglas para imágenes y texto asociado

- Una imagen semántica debe estar junto al ítem, ejemplo o lectura que representa; no se agrupan todas las imágenes al comienzo de una página.
- La interfaz muestra las imágenes referenciadas por la propuesta de la página para permitir cotejo visual.
- Las imágenes decorativas pueden omitirse con justificación editorial. No se mantienen recursos en el ZIP que no estén referenciados en XML.
- Se corrigió el caso `PHE27_SE_L05_p049_01.png`: era una franja decorativa no incluida en XML; se eliminó del ZIP final y del OPF generado.
- Hay una excepción documentada de nomenclatura heredada: `PHE27_SE_L19_p226_03.png` se relaciona semánticamente con el ítem 4 de la página 225, aunque su nombre sugiera la 226.
- Las leyendas de imágenes se asocian con `caption imgref`; los saltos de línea internos de una leyenda usan `<br/>` cuando el PDF presenta dos líneas significativas.

### 5. Hojas de respuesta y ejemplos

- Los espacios de respuesta usan `span class="WOL"` con guiones bajos reales; no deben ser spans vacíos.
- Los ejemplos conservan la respuesta sólo cuando el PDF la muestra como parte del ejemplo.
- Una respuesta marcada gráficamente (por ejemplo, una opción encerrada) se representa dentro del contenido accesible del ejemplo, no como una nota editorial de profesor ni como `prodnote` usado para captions.

### 6. Correcciones de validez DTBook

- No se permite `<imggroup>` dentro de `<p>`; debe ser un bloque hermano, antes o después del párrafo según el PDF.
- Cada `level3` necesita un encabezado y contenido posterior; se corrigieron actividades que sólo contenían `h3` y por tanto fallaban el DTD.
- No se usan entidades HTML como `&nbsp;` en XML. Las alternativas de respuesta se estructuran como listas/opciones, no mediante espacios de relleno.
- Se eliminaron envoltorios `div` innecesarios para mantener el patrón NIMAS/DTBook más conservador.

## Frontmatter y rear matter

### Frontmatter (FM)

- Se propuso y auditó completo para las páginas editoriales con contenido i–vii.
- La página final viii, sin contenido editorial útil, no se exporta como contenido.
- Se preservan `doctitle`, `docauthor` y la estructura de frontmatter del paquete.

### Rear matter (EM)

- Fue reconstruido desde el PDF porque el XML fuente no coincidía con los folios del PDF y contenía páginas fuera de rango.
- La propuesta abarca 287–297; se excluyen las páginas finales en blanco 298–304.
- Jerarquía aplicada: un `h1` para `CREDITS`, `h2` para `Photography and Art Credits` y `h3` para cada lección; para el índice, un `h1` para `INDEX`, `h2` para grupos de letra y `h3` para entradas.

## Cambios requeridos en la aplicación

1. **Panel de proyecto y estado**
   - Mostrar FM, EM y las lecciones como unidades auditables.
   - Diferenciar patrón humano, pendiente, lista para auditoría, reconstrucción requerida y aprobada.
   - La aprobación es por unidad completa, no mediante checklists obligatorios por página.

2. **Auditoría por página**
   - Navegación anterior/siguiente fija y teclado con flechas.
   - PDF en el centro, propuesta a la derecha y fuente como referencia secundaria.
   - Carrusel/panel de imágenes realmente referenciadas en la propuesta de la página.

3. **Agente y solicitudes de ajuste**
   - Un ajuste solicitado desde una página se debe aplicar sólo a esa página, sin regenerar toda la lección.
   - Debe quedar historial de propuesta anterior y solicitud editorial.
   - Debe existir un indicador de tarea en curso y una notificación al completar o fallar una generación.

4. **Detección y recuperación automática**
   - Comparar rangos de pagenum esperados contra el PDF antes de ofrecer aprobación.
   - Si falta contenido, páginas o estructura, marcar “reconstrucción desde PDF requerida”.
   - Nunca aceptar automáticamente la fuente sólo porque existe XML.

5. **Exportación final protegida**
   - Sólo se habilita cuando las lecciones y FM/EM requeridos estén aprobados.
   - Ensamblar desde un XML/OPF base válido, no desde un paquete de progreso potencialmente mal formado.
   - Incorporar FM, lecciones y EM aprobados dentro de `frontmatter`, `bodymatter` y `rearmatter` respectivamente.
   - Reconstruir el manifiesto OPF desde los recursos realmente referenciados por el XML.
   - Excluir imágenes físicas sin referencia XML y archivos de sistema como `.DS_Store`.
   - Validar: XML bien formado, DTD DTBook 2005-3, secuencia de páginas, archivos de imagen existentes, cada `img/@src` declarado en OPF, y ZIP íntegro.
   - Crear una carpeta y ZIP con sello de fecha; nunca sobrescribir las fuentes.

6. **Formato de salida**
   - XML y OPF con cada etiqueta alineada a la izquierda: sin tabulaciones ni espacios iniciales.
   - El OPF debe conservar un elemento por línea, particularmente cada `<item>` del `<manifest>`.

## Criterio de aceptación del desarrollador

La implementación estará lista para entrega editorial cuando la app pueda generar un ZIP que cumpla simultáneamente lo siguiente:

- El XML final valida contra DTBook 2005-3.
- El OPF es XML válido y contiene todos —y sólo— los recursos de imagen usados por DTBook.
- El PDF y la propuesta se pueden comparar por página desde la interfaz.
- Los rangos inconsistentes se detienen y se ofrecen para recuperación basada en PDF.
- No hay imágenes huérfanas, niveles sin contenido, contenido visual agrupado sin relación semántica ni entidades HTML inválidas.
- El ZIP no modifica los paquetes fuente y queda disponible para descargar con su informe de validación.
