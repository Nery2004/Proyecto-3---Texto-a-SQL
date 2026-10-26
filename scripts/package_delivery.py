"""ZIP reproducible de entrega sin entorno, credenciales, cachés ni checkpoints."""
import argparse
import json
from pathlib import Path
import zipfile

def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',default='entrega_proyecto3.zip')
    parser.add_argument('--allow-partial',action='store_true')
    args=parser.parse_args()
    root=Path('.').resolve();target=Path(args.output).resolve()
    missing=[p.relative_to(root).as_posix() for p in [root/'adapter/adapter_config.json',root/'adapter/adapter_model.safetensors',root/'presentacion.pdf'] if not p.is_file()]
    if missing and not args.allow_partial:
        raise RuntimeError('Entrega incompleta: '+', '.join(missing))
    excluded={'.git','.venv','.runtime','.pytest_cache','__pycache__','checkpoints'}
    included=[]
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(root.rglob('*')):
            relative=file.relative_to(root)
            if not file.is_file() or file.resolve()==target or not file.resolve().is_relative_to(root):continue
            if any(part in excluded for part in relative.parts):continue
            if file.name.startswith('.env') or file.suffix in {'.log','.pyc','.zip'}:continue
            archive.write(file,'proyecto3/'+relative.as_posix());included.append(relative.as_posix())
        audit=root/'resultados/metricas/auditoria_entrega.json'
        project_status=json.loads(audit.read_text(encoding='utf-8')).get('estado_general','SIN_AUDITAR') if audit.exists() else 'SIN_AUDITAR'
        archive.writestr('proyecto3/ESTADO_ZIP.json',json.dumps({'parcial':bool(missing) or project_status!='COMPLETO','faltantes_fisicos':missing,'estado_proyecto':project_status,'nota':'No contiene credenciales ni pesos base HF. Descargar modelo indicado en config.json. Revisar docs/estado_ejecucion.md para requisitos externos.'},indent=2))
    print(f'{target.name}: {len(included)} archivos; {target.stat().st_size} bytes; parcial={bool(missing)}')

if __name__=='__main__':main()
