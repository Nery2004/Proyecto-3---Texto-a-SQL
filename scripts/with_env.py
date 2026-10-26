"""Ejecuta un comando usando .env local sin mostrar sus valores."""
import os
from pathlib import Path
import subprocess
import sys

def load_env(path='.env'):
    if Path(path).exists():
        for line in Path(path).read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                key,value=line.split('=',1)
                os.environ.setdefault(key.strip(),value.strip().strip('\"').strip("'"))

if __name__=='__main__':
    load_env()
    if len(sys.argv)<2:
        raise SystemExit('Uso: python -m scripts.with_env COMANDO [ARGUMENTOS]')
    raise SystemExit(subprocess.call(sys.argv[1:]))
