#!/bin/zsh
# Genera una propuesta completa de una lección mediante Codex CLI.
# No instala ni reemplaza el XML aprobado: sólo escribe lecciones_propuestas/LNN.xml.

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 || ! "$1" =~ '^[0-9]+$' || "$1" -lt 4 || "$1" -gt 24 || ( $# -eq 2 && ! "$2" =~ '^[0-9]+$' ) ]]; then
  print -u2 "Uso: ./nimas-agent/generar_propuesta_leccion.sh NUMERO_DE_LECCION (4-24) [PAGINA]"
  exit 64
fi

lesson=$(printf '%02d' "$1")
page=${2:-}
root_dir=${0:A:h:h}
source_xml="$root_dir/lecciones_originales/L${lesson}.xml"
pdf=$(find "$root_dir/PDF" -maxdepth 1 -type f -name "PHE27_SE_L${lesson}_*.pdf" -print -quit)
output_xml="$root_dir/lecciones_propuestas/L${lesson}.xml"
run_dir="$root_dir/nimas-review/agent-runs"
codex_bin="/Applications/ChatGPT.app/Contents/Resources/codex"

[[ -f "$source_xml" ]] || { print -u2 "No existe: $source_xml"; exit 66; }
[[ -n "$pdf" ]] || { print -u2 "No se encontró el PDF de L${lesson}"; exit 66; }
[[ -x "$codex_bin" ]] || { print -u2 "No se encontró Codex CLI: $codex_bin"; exit 69; }

mkdir -p "$root_dir/lecciones_propuestas" "$run_dir"
python3 "$root_dir/nimas-agent/auditar_rangos_editoriales.py" > "$run_dir/rangos-editoriales.json"

PATH="$root_dir/nimas-agent/bin:$PATH" "$codex_bin" exec \
  --sandbox workspace-write \
  --skip-git-repo-check \
  --ephemeral \
  -C "$root_dir" \
  -o "$run_dir/L${lesson}-resultado.md" <<PROMPT
${page:+Corrige únicamente la página ${page} de la propuesta editorial NIMAS de la lección ${lesson}.}
${page:-Remedia por completo la lección ${lesson} como propuesta editorial NIMAS.}

Fuentes obligatorias:
- XML original: lecciones_originales/L${lesson}.xml
- PDF editorial: ${pdf#$root_dir/}
- Tres patrones humanos: lecciones_remediadas/L01.xml, L02.xml, L03.xml
- Manual obligatorio: nimas-review/manual-aprendizaje-agente.md
- Solicitudes editoriales previas de esta lección, si existen: nimas-review/solicitudes-ajuste/L${lesson}-p*.md
- Auditoría automática de rango PDF/XML: nimas-review/agent-runs/rangos-editoriales.json
${page:+- Propuesta existente que debes conservar: lecciones_propuestas/L${lesson}.xml}

Resultado obligatorio:
- Escribe exactamente un fragmento XML bien formado en
  lecciones_propuestas/L${lesson}.xml, cuyo elemento raíz sea level1. No
  incluyas declaración XML, doctype, dtbook, book ni bodymatter.
- Debe contener exactamente un level1 para toda la lección. Los pagenum son
  anclas dentro de ese level1; nunca niveles o documentos por página.
${page:+- Trabaja sólo desde el pagenum ${page} hasta el pagenum siguiente. Conserva sin cambios el resto de la propuesta, incluidos niveles que se abren o cierran fuera de esa página. No reinterpretes ni regeneres otras páginas.}
- Consulta el PDF visualmente página por página; no infieras estructura sólo
  desde OCR/XML.
- Si una utilidad auxiliar de imagen no está disponible, continúa con
  pdftoppm y la inspección individual de las páginas; no abandones la
  propuesta por no poder crear una hoja de contactos.
- Aplica el manual para títulos, actividades, tablas, listas, sidebars,
  examples, WOL, capturas/captions de imágenes y Decodable Reader. En una
  caption de una transformación mostrada en dos renglones, conserva ambas
  líneas en una sola caption con <br/> (por ejemplo, play + ing<br/>playing).
- En el panel 8 de cada Decodable Reader, el número es parte del primer
  párrafo: usa exactamente la secuencia li / p «8. Decodable Words» / p
  «[banco]» / p «High Frequency Words» / p «Focus: …» / p «Others: …».
  Nunca dejes el texto «8.» suelto antes del primer p.
- Mantén el texto del PDF, no inventes contenido y no cambies archivos en
  9781669952961NIMAS, 9781669952961NIMAS_original, lecciones_originales,
  lecciones_remediadas, auditoria-lecciones ni nimas-review.
- Lee y aplica todas las solicitudes editoriales guardadas para esta lección.
  Son correcciones humanas específicas; no las ignores ni las borres.
- Lee la auditoría de rango. Si L${lesson} está marcada como \`required\`, entra
  en modo de recuperación: el rango del PDF sustituye la delimitación del XML,
  recuperas desde el PDF cada página faltante y documentas la discrepancia en
  \`nimas-review/agent-runs/L${lesson}-discrepancia-de-rango.md\`.
- Puedes leer las imágenes de 9781669952961NIMAS/images/L${lesson} para usar
  los recortes disponibles, pero sólo referencia recursos que existan.
- Valida al final con xmllint --noout lecciones_propuestas/L${lesson}.xml,
  python3 nimas-agent/auditar_recursos_sin_referenciar.py ${lesson} y
  python3 nimas-agent/auditar_asociacion_imagenes.py ${lesson}. Si el auditor
  detecta un grupo de dos o más imágenes junto a una lista, consulta el PDF y
  estructura la relación antes de entregar la propuesta. La diferencia de
  cantidades no es una excepción: puede ser una imagen de ejemplo más los
  ítems. Mantén el ejemplo mediante sus propios p e imggroup, directamente
  dentro del level correspondiente, y coloca cada imagen restante dentro de
  su li, o usa un banco de opciones independiente sólo si
  el PDF muestra realmente un ejercicio de relación.
- Si una parte es ambigua, conserva la incertidumbre en
  nimas-review/agent-runs/L${lesson}-dudas.md, pero entrega la mejor propuesta
  completa y no dejes una lección parcial.
PROMPT

python3 "$root_dir/nimas-agent/validar_propuesta_leccion.py" "$lesson"
print "Propuesta creada: $output_xml"
