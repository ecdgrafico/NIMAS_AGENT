# Propuesta semántica: Lesson 1

Estado: pendiente de revisión editorial. Esta propuesta se deriva del PDF `PHE27_SE_L01_001-012_hi.pdf`; no modifica el XML.

## Criterio rector

`Lesson 1` es el único `level1` de las páginas 1–12. `pagenum` conserva cada cambio de página, pero no abre ni cierra una jerarquía lógica. El título de la lección es el único `h1`.

Los temas didácticos nombrados son secciones de segundo nivel (`level2`/`h2`). Las actividades con letras permanecen dentro de su tema y sus instrucciones son párrafos, comenzando por la letra de actividad. Cuando una actividad se prolonga a la página siguiente, continúa en el mismo nivel.

## Mapa propuesto

| Páginas | Nivel y encabezado | Contenido subordinado |
| --- | --- | --- |
| 1 | `level1` / `h1`: **Lesson 1** | `level2` / `h2`: **IN THIS LESSON** con la tabla de contenidos didácticos; `level2` / `h2`: **Matt and the Bat** con su texto e imagen. |
| 2 | `level2` / `h2`: **Consonants: s, m** | Instrucción auditiva en `p`; presentación de S/s y M/m con sus imágenes y palabras; actividades A, B y C en `p` seguidas de sus listas, opciones e imágenes relacionadas. |
| 3 | `level2` / `h2`: **Consonants: b, t** | Mismo patrón: instrucción, presentación b/t, actividades A–C. “Say words that begin with b and t” es continuación de C, no `h2`. |
| 4 | `level2` / `h2`: **Consonants: s, m, b, t** | Actividades A y B. La cuadrícula de respuestas se conserva como tabla solo si refleja posiciones relevantes; de lo contrario, una lista ordenada con opciones/blancos. |
| 5–6 | `level2` / `h2`: **Short Vowel: a** | Instrucción y presentación de A/a; actividades A–F. D/E/F de la página 6 continúan este nivel; no son encabezados `h2`. |
| 7–8 | `level2` / `h2`: **Digraph: th** | Instrucción y presentación de `th`; actividades A–E. C/D/E de página 8 continúan el mismo tema. |
| 9–10 | `level2` / `h2`: **Decodable Reader: The Bats** | Secuencia de lectura en orden narrativo 1–8, no en el orden de extracción visual. **Decodable Words** y **High Frequency Words** son rótulos de contenido dentro de la sección, propuestos como `h3` si se desea navegación directa; de lo contrario, `p` destacados. |
| 11–12 | `level2` / `h2`: **Decodable Reader Activities** | Actividades A–D como párrafos/instrucciones con listas y tablas apropiadas. C y D pertenecen a la misma sección, aunque estén en otra página. |

## Ajustes de lectura y semántica observados

1. Página 2: `Listen to the letter sounds...` es instrucción, no `h1`; **Consonants: s, m** debe precederla como `h2`.
2. Páginas 2–8: las letras de actividad A–F deben permanecer asociadas con sus indicaciones; no deben convertirse en niveles de documento salvo decisión editorial futura.
3. Páginas 9–10: la secuencia del lector debe seguir el orden narrativo impreso 1–8, aun cuando el PDF se extraiga en otro orden.
4. En todo el rango: Name, Date, LESSON 1 recurrente, folio, copyright y marcas de producción son material de página y se excluyen de la lectura principal.
5. Las imágenes mantienen `alt=""`, conforme a la política del proyecto. Deben conservar identificadores únicos, rutas válidas y manifestación en OPF.

## Decisiones que requieren tu visto bueno

- ¿Deseas `h3` para **Decodable Words** y **High Frequency Words**, o que ambos queden como texto destacado sin navegación?
- ¿Las etiquetas A–F deben permanecer como texto al inicio de la instrucción —propuesta actual— o quieres que sean encabezados navegables de tercer nivel?
- ¿La tabla “IN THIS LESSON” debe seguir siendo tabla, como propone esta ficha, o prefieres una lista de categorías y destrezas?
