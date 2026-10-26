"""Extract actual progress from Trainer logs without touching the training process."""
import argparse
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time


def update_progress(log, output):
    raw = Path(log).read_bytes()
    source = raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8', errors='replace')
    steps = re.findall(r'(\d+)/(\d+) \[([^<\]]+)<([^,\]]+),\s*([\d.]+)s/it\]', source)
    losses = []
    for match in re.findall(r"\{'loss':[^\n\r]+?\}", source):
        try:
            losses.append(ast.literal_eval(match))
        except (ValueError, SyntaxError):
            pass
    path = Path(output)
    report = {'estado': 'en_curso', 'fuente_log': str(log), 'actualizado_utc': datetime.now(timezone.utc).isoformat(),
              'paso_observado': int(steps[-1][0]) if steps else 0,
              'pasos_totales': int(steps[-1][1]) if steps else None,
              'segundos_por_paso_observados': float(steps[-1][4]) if steps else None,
              'tiempo_transcurrido_entrenador': steps[-1][2] if steps else None,
              'tiempo_restante_estimado_entrenador': steps[-1][3] if steps else None,
              'ultimo_loss_observado': losses[-1] if losses else None,
              'nota': 'TQDM y loss reales del log; las estimaciones de tiempo pueden cambiar. Loss null indica stdout aun sin registro visible.'}
    final = path.parent / 'run.json'
    if final.exists():
        report['estado'] = json.loads(final.read_text(encoding='utf-8'))['estado']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--log', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--watch', action='store_true', help='Actualizar cada 30s hasta run.json final')
    args = parser.parse_args()
    while True:
        report = update_progress(args.log, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
        if not args.watch or report['estado'] in {'completado', 'fallido'}:
            break
        time.sleep(30)
