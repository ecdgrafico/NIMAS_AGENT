#!/bin/zsh
# Genera una propuesta editorial de FM o EM sin alterar el XML fuente.

set -euo pipefail

if [[ $# -ne 1 || ( "$1" != "FM" && "$1" != "EM" ) ]]; then
  print -u2 "Uso: ./nimas-agent/generar_propuesta_seccion.sh FM|EM"
  exit 64
fi

section="$1"
root_dir=${0:A:h:h}
source_xml="$root_dir/lecciones_originales/${section}.xml"
pdf="$root_dir/PDF/PHE27_SE_${section}_$( [[ "$section" == "FM" ]] && print 'i-iv' || print '287-304' )_hi.pdf"
output_xml="$root_dir/secciones_propuestas/${section}.xml"
run_dir="$root_dir/nimas-review/agent-runs"
codex_bin="/Applications/ChatGPT.app/Contents/Resources/codex"

[[ -f "$source_xml" ]] || { print -u2 "No existe: $source_xml"; exit 66; }
[[ -f "$pdf" ]] || { print -u2 "No existe: $pdf"; exit 66; }
[[ -x "$codex_bin" ]] || { print -u2 "No se encontró Codex CLI: $codex_bin"; exit 69; }

mkdir -p "$root_dir/secciones_propuestas" "$run_dir"
python3 "$root_dir/nimas-agent/auditar_rangos_editoriales.py" > "$run_dir/rangos-editoriales.json"

PATH="$root_dir/nimas-agent/bin:$PATH" "$codex_bin" exec \
  --sandbox workspace-write \
  --skip-git-repo-check \
  --ephemeral \
  -C "$root_dir" \
  -o "$run_dir/${section}-resultado.md" <<PROMPT
Construye una propuesta editorial NIMAS de ${section}, independiente del XML fuente.

Fuentes obligatorias:
- XML original: lecciones_originales/${section}.xml
- PDF editorial: ${pdf#$root_dir/}
- Manual: nimas-review/manual-aprendizaje-agente.md
- Auditoría de rango: nimas-review/agent-runs/rangos-editoriales.json

Resultado obligatorio:
- Escribe exclusivamente la propuesta en secciones_propuestas/${section}.xml.
- No incluyas declaración XML, doctype, dtbook, book, bodymatter ni rearmatter.
- Es un fragmento para integrarse más adelante: puede contener varios level1 consecutivos; no inventes un contenedor artificial sólo para que sea un documento autónomo.
- El PDF es la autoridad visual. Conserva del XML sólo texto, IDs y referencias de recursos que realmente correspondan con el PDF.
- Reconstruye todo el contenido editorial visible: para FM i–vii (omite la página viii final en blanco); para EM 287–297 (omite las páginas 298–304 finales en blanco). No incorpores páginas fuera de esos rangos ni imágenes de hojas blancas.
- Usa jerarquía DTBook semántica y conserva pagenum. Corrige TOC, créditos y listas cuando el PDF lo requiera.
- No modifiques fuentes, lecciones, propuestas de lecciones ni recursos del paquete.
- Documenta incertidumbres en nimas-review/agent-runs/${section}-dudas.md, pero entrega siempre la mejor propuesta completa.
PROMPT

print "Propuesta creada: $output_xml"
