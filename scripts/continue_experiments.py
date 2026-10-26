"""Continue an already running A experiment, then B and comparable evaluation.

This supervisor never runs two model processes at once. Run from repository root.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

from scripts.training_progress import update_progress


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--wait-pid', type=int, required=True, help='PID of the already running A Python process')
    parser.add_argument('--dataset', default='datos/validacion/evaluacion_48.jsonl')
    args = parser.parse_args()
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('MKL_NUM_THREADS', '1')
    os.environ['PYTHONUNBUFFERED'] = '1'
    state_path = Path('resultados/metricas/orquestacion_experimentos.json')
    state_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    state = {'estado': 'en_curso', 'fase': 'esperando_A', 'pid_A': args.wait_pid,
             'inicio_utc': datetime.now(timezone.utc).isoformat()}

    def save():
        state['actualizado_utc'] = datetime.now(timezone.utc).isoformat()
        state['segundos_supervisor'] = time.perf_counter() - started
        state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')

    def require_completed(path):
        run = json.loads(Path(path).read_text(encoding='utf-8'))
        if run['estado'] != 'completado':
            raise RuntimeError(f'Entrenamiento sin completar: {path}: {run.get("error")}')
        return run

    save()
    try:
        if psutil.pid_exists(args.wait_pid):
            process = psutil.Process(args.wait_pid)
            while process.is_running():
                try:
                    process.wait(timeout=30)
                    break
                except psutil.TimeoutExpired:
                    save()
        a = require_completed('adapters_experimentos/config_a/run.json')
        dataset = Path(a['config']['dataset'])
        if hashlib.sha256(dataset.read_bytes()).hexdigest() != a['dataset_sha256']:
            raise RuntimeError('Dataset de entrenamiento cambió entre A y B')
        before = json.loads(Path('resultados/baseline_pre_entrenamiento/manifest_evaluacion.json').read_text(encoding='utf-8'))
        if hashlib.sha256(Path(args.dataset).read_bytes()).hexdigest() != before['dataset_sha256']:
            raise RuntimeError('Validación cambió después del baseline')
        state['fase'] = 'entrenamiento_B'
        with Path('train-b.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen([sys.executable, '-u', '-m', 'scripts.train', '--config', 'configs/lora_b.json'], stdout=log, stderr=subprocess.STDOUT)
            state['pid_B'] = process.pid
            save()
            while process.poll() is None:
                time.sleep(30)
                if 's/it]' in Path('train-b.log').read_text(encoding='utf-8', errors='replace'):
                    update_progress('train-b.log', 'adapters_experimentos/config_b/progreso.json')
                save()
        b = require_completed('adapters_experimentos/config_b/run.json')
        update_progress('train-b.log', 'adapters_experimentos/config_b/progreso.json')
        if a['dataset_sha256'] != b['dataset_sha256']:
            raise RuntimeError('Hashes A/B diferentes')
        state['fase'] = 'evaluacion_3_modelos'
        save()
        from scripts.with_env import load_env
        load_env()
        command = [sys.executable, '-u', 'scripts/evaluate.py', '--dataset', args.dataset,
                   '--config', 'configs/baseline.json', '--config', 'configs/inference_a.json',
                   '--config', 'configs/inference_b.json', '--strategy', 'ambas']
        with Path('evaluation-final.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f'Evaluación falló con exit code {result.returncode}; consultar evaluation-final.log')
        state.update(estado='completado', fase='completado')
    except Exception as exc:
        state.update(estado='fallido', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        save()


if __name__ == '__main__':
    main()
