#!/usr/bin/env python3
"""Generate a review-only DTBook proposal with an available AI provider."""
import argparse, shutil, subprocess, sys
from pathlib import Path
from ai_provider import provider_status, write_prompt
from ai_provider import find_ollama

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project',type=Path,required=True); ap.add_argument('--unit',required=True); ap.add_argument('--provider',default='codex'); args=ap.parse_args()
    root=args.project.resolve(); prompt=Path(write_prompt(root,args.unit)); output=root/'propuestas'/f'{args.unit}.xml'; runlog=root/'versions'/'ai-runs'; runlog.mkdir(parents=True,exist_ok=True)
    instruction=prompt.read_text(encoding='utf-8')+f'''\n\nEscribe únicamente un fragmento XML DTBook bien formado en {output}. No modifiques fuentes. Si no puedes verificar una parte, conserva la incertidumbre en {runlog/(args.unit+'-dudas.md')}. La salida queda pendiente de auditoría humana.'''
    if args.provider=='codex':
        executable=shutil.which('codex')
        if not executable: raise SystemExit('Codex CLI no está disponible en PATH.')
        instruction_path=runlog/(args.unit+'-instruction.md'); instruction_path.write_text(instruction,encoding='utf-8')
        short_instruction=f'Read and follow the complete instructions in {instruction_path}. Create the requested XML proposal and do not modify source files.'
        result=subprocess.run([executable,'exec','--sandbox','workspace-write','--add-dir',str(root),'--skip-git-repo-check','--ephemeral','-C',str(root),'-o',str(runlog/(args.unit+'-codex.md')),short_instruction],cwd=root,text=True,capture_output=True)
    elif args.provider=='ollama':
        executable=find_ollama()
        if not executable: raise SystemExit('Ollama no está disponible en PATH.')
        model = __import__('os').environ.get('NIMAS_OLLAMA_MODEL','llama3.2')
        # Send the prompt through stdin so long PDF/XML evidence never hits
        # Windows' command-line length limit.
        result=subprocess.run([executable,'run',model],cwd=root,input=instruction,text=True,encoding='utf-8',capture_output=True)
        if result.returncode==0 and not output.is_file():
            text=result.stdout.strip(); text=text.removeprefix('```xml').removesuffix('```').strip(); output.write_text(text+'\n',encoding='utf-8')
            (runlog/(args.unit+'-ollama.md')).write_text(result.stdout,encoding='utf-8')
    else:
        raise SystemExit('Proveedor no soportado: '+args.provider)
    if result.returncode: raise SystemExit(result.stderr.strip() or result.stdout.strip() or 'Codex no generó la propuesta.')
    if not output.is_file():
        diagnostic=(runlog/(args.unit+'-codex.md')).read_text(encoding='utf-8',errors='replace')[-1000:] if (runlog/(args.unit+'-codex.md')).is_file() else ''
        raise SystemExit(f'Codex terminó sin crear {output}. Diagnóstico: {diagnostic}')
    report = runlog / f'{args.unit}-validation.json'
    check = subprocess.run([sys.executable, str(Path(__file__).with_name('validate_ai_proposal.py')), str(output), '--report', str(report)], cwd=root, text=True, capture_output=True)
    if check.returncode: raise SystemExit(f'La propuesta quedó pendiente por errores de estructura. Revisa {report}')
    print(f'Propuesta pendiente creada: {output}')

if __name__=='__main__': main()
