#!/usr/bin/env python3
"""Create a NIMAS ZIP only after the preflight report passes."""
import argparse, json, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('package',type=Path); p.add_argument('report',type=Path); p.add_argument('zip',type=Path); a=p.parse_args()
result=json.loads(a.report.read_text())
if result['status'] != 'pass': sys.exit('Refusing to package: audit is blocked.')
subprocess.run(['zip','-qry',str(a.zip),a.package.name,'-x','*/.DS_Store','.DS_Store'],cwd=a.package.parent,check=True)
