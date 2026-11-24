#!/usr/bin/env python3
"""Generate a review-only DTBook proposal with an available AI provider."""
import argparse, shutil, subprocess, sys
from pathlib import Path
from ai_provider import provider_status, write_prompt

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project',type=Path,required=True); ap.add_argument('--unit',required=True); ap.add_argument('--provider',default='codex'); args=ap.parse_args()
    root=args.project.resolve(); prompt=Path(write_prompt(root,args.unit)); output=root/'propuestas'/f'{args.unit}.xml'; runlog=root/'versions'/'ai-runs'; runlog.mkdir(parents=True,exist_ok=True)
    if args.provider!='codex': raise SystemExit('Este ejecutor inicial soporta Codex; Ollama quedará como adaptador siguiente.')
    codex=shutil.which('codex')
    if not codex: raise SystemExit('Codex CLI no está disponible en PATH.')
    instruction=prompt.read_text(encoding='utf-8')+f'''\n\nEscribe únicamente un fragmento XML DTBook bien formado en {output}. No modifiques fuentes. Si no puedes verificar una parte, conserva la incertidumbre en {runlog/(args.unit+'-dudas.md')}. La salida queda pendiente de auditoría humana.'''
    result=subprocess.run([codex,'exec','--sandbox','workspace-write','--skip-git-repo-check','--ephemeral','-C',str(root),'-o',str(runlog/(args.unit+'-codex.md')),instruction],cwd=root,text=True,capture_output=True)
    if result.returncode: raise SystemExit(result.stderr.strip() or result.stdout.strip() or 'Codex no generó la propuesta.')
    if not output.is_file(): raise SystemExit(f'Codex terminó sin crear {output}')
    report = runlog / f'{args.unit}-validation.json'
    check = subprocess.run([sys.executable, str(Path(__file__).with_name('validate_ai_proposal.py')), str(output), '--report', str(report)], cwd=root, text=True, capture_output=True)
    if check.returncode: raise SystemExit(f'La propuesta quedó pendiente por errores de estructura. Revisa {report}')
    print(f'Propuesta pendiente creada: {output}')

if __name__=='__main__': main()
