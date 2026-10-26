"""Extract actual progress from Trainer logs without touching the training process."""
import argparse
import ast
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time


def safe_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: safe_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [safe_json(item) for item in value]
    return value


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
    update_checks = []
    audit = Path('resultados/curvas_entrenamiento') / path.parent.name / 'logs.jsonl'
    if audit.exists():
        for line in audit.read_text(encoding='utf-8').splitlines():
            try:
                item = json.loads(line)
                if 'loss' in item:
                    losses.append(item)
                if 'lora_b_no_cero' in item:
                    update_checks.append(item)
            except ValueError:
                pass
    # Redirected Python stdout can stay buffered for many minutes on Windows.
    # Trainer checkpoints preserve actual log_history independently of stdout.
    for checkpoint in (path.parent / 'checkpoints').glob('checkpoint-*/trainer_state.json'):
        try:
            history = json.loads(checkpoint.read_text(encoding='utf-8'))['log_history']
            losses.extend(item for item in history if 'loss' in item)
        except (OSError, ValueError, KeyError):
            pass  # A checkpoint may still be in the middle of a save.
    losses.sort(key=lambda item: item.get('epoch', 0))
    report = {'estado': 'en_curso', 'fuente_log': str(log), 'actualizado_utc': datetime.now(timezone.utc).isoformat(),
              'paso_observado': int(steps[-1][0]) if steps else 0,
              'pasos_totales': int(steps[-1][1]) if steps else None,
              'segundos_por_paso_observados': float(steps[-1][4]) if steps else None,
              'tiempo_transcurrido_entrenador': steps[-1][2] if steps else None,
              'tiempo_restante_estimado_entrenador': steps[-1][3] if steps else None,
              'ultimo_loss_observado': losses[-1] if losses else None,
              'verificacion_actualizacion': update_checks[-1] if update_checks else None,
              'nota': 'TQDM y loss reales del log/checkpoint Trainer. Las estimaciones de tiempo pueden cambiar. Loss null indica que aun no hay registro visible; epoch/step del loss identifica su antiguedad.'}
    final = path.parent / 'run.json'
    if final.exists():
        report['estado'] = json.loads(final.read_text(encoding='utf-8'))['estado']
    path.parent.mkdir(parents=True, exist_ok=True)
    report = safe_json(report)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
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
