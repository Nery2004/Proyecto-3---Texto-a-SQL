"""Run comparable real-model, real-MySQL evaluations; no synthetic scores."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation import evaluate, summarize, write_reports
from src.evaluation.runner import write_csv, grouped_summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="datos/validacion/validacion.jsonl")
    parser.add_argument("--config", action="append", required=True,
                        help="JSON config; repeat for baseline/LoRA comparisons")
    parser.add_argument("--executor-factory", default="src.data.mysql:MySQLExecutor",
                        help="module:function mapping schema_id to read-only callback")
    parser.add_argument("--output", default="resultados")
    parser.add_argument("--strategy", choices=["directa", "callback", "ambas"], default="ambas")
    args = parser.parse_args()
    configurations = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.config]
    shared = {(config["modelo_base"], config["semilla"]) for config in configurations}
    if len(shared) != 1:
        parser.error("Comparación requiere el mismo modelo base y semilla")
    examples = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not examples:
        parser.error("Dataset vacío")
    module, name = args.executor_factory.split(":")
    factory = getattr(importlib.import_module(module), name)
    from solucion import generar_sql
    from src.inference.engine import get_runtime
    strategies = ["directa", "callback"] if args.strategy == "ambas" else [args.strategy]
    all_records, summaries = [], []
    from src.inference.prompt import VERSION
    manifest = {"dataset": args.dataset,
                "dataset_sha256": hashlib.sha256(Path(args.dataset).read_bytes()).hexdigest(),
                "prompt_version": VERSION, "configuraciones": configurations,
                "nota_autoria": "Propuestas IA; revisar autoría humana antes de entrega académica"}
    Path(args.output).mkdir(parents=True, exist_ok=True)
    (Path(args.output) / "manifest_evaluacion.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for config in args.config:
        os.environ["TEXT2SQL_CONFIG"] = str(Path(config).resolve())
        started = perf_counter()
        get_runtime()
        load_seconds = perf_counter() - started
        if load_seconds > 300:
            raise RuntimeError(f"Carga excede 300 segundos: {config}: {load_seconds:.3f}")
        label = Path(config).stem
        for strategy in strategies:
            records = evaluate(examples, generar_sql, factory, model=label, strategy=strategy)
            is_baseline = not json.loads(Path(config).read_text(encoding="utf-8"))["usar_adapter"]
            filename = "baseline.csv" if is_baseline and strategy == "directa" else f"{label}_{strategy}.csv"
            summary = write_reports(records, args.output, filename)
            summary.update(modelo=label, estrategia=strategy, carga_segundos=load_seconds)
            summaries.append(summary)
            all_records.extend(records)
    write_csv(Path(args.output) / "comparacion_lora.csv", all_records)
    write_csv(Path(args.output) / "validacion_propia.csv", all_records)
    write_csv(Path(args.output) / "errores.csv", [r for r in all_records if not r["resultado_correcto"]], list(all_records[0]))
    write_csv(Path(args.output) / "resumen_comparacion.csv", summaries)
    write_csv(Path(args.output) / "resumen_por_dificultad_modelo.csv", grouped_summary(all_records))
    plot_comparison(summaries, args.output)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


def plot_comparison(summaries, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels = [f"{r['modelo']}\n{r['estrategia']}" for r in summaries]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(labels, [r["ex_ponderada"] for r in summaries])
    axes[0].set(ylabel="EX ponderada", ylim=(0, 1))
    axes[1].bar(labels, [r["latencia_promedio"] for r in summaries])
    axes[1].set(ylabel="Segundos promedio")
    fig.tight_layout()
    fig.savefig(Path(directory) / "comparacion.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
