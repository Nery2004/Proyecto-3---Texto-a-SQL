"""Precarga real con evidencia de tiempo/errores; no genera métricas de EX."""
import argparse
import json
import os
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--config', default='configs/baseline.json')
    parser.add_argument('--output', default='resultados/metricas/carga_baseline.json')
    args = parser.parse_args()
    os.environ['TEXT2SQL_CONFIG'] = str(Path(args.config).resolve())
    started = time.perf_counter()
    report = {'config': args.config, 'estado': 'iniciado'}
    try:
        from src.inference.engine import get_runtime
        runtime = get_runtime()
        report.update(estado='completado', carga_modelo_segundos=runtime.load_seconds)
    except Exception as exc:
        report.update(estado='fallido', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['segundos_totales'] = time.perf_counter() - started
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
