"""Evaluation orchestration with auditable per-question callback budgets."""
import csv
import json
from collections import defaultdict
from pathlib import Path
from time import perf_counter

from .metrics import compare_results, weighted_ex


def structural_differences(reference_sql, generated_sql):
    """AST differences suggest error causes; they never determine correctness."""
    import sqlglot
    from sqlglot import exp
    try:
        trees = [sqlglot.parse_one(sql, read="mysql") for sql in (reference_sql, generated_sql)]
    except sqlglot.errors.ParseError:
        return []
    groups = {"join_incorrecto": (exp.Join,),
              "agregacion_incorrecta": (exp.AggFunc, exp.Group, exp.Having),
              "filtro_incorrecto": (exp.Where,)}
    differences = []
    for category, classes in groups.items():
        signatures = [sorted(node.sql(dialect="mysql", normalize=True)
                             for node in tree.walk() if isinstance(node, classes)) for tree in trees]
        if signatures[0] != signatures[1]:
            differences.append(category)
    return differences


def error_category(error, reference_sql="", generated_sql=""):
    text = str(error).lower()
    for needles, category in [(("1064", "syntax"), "sintaxis"),
                              (("1146", "doesn't exist", "unknown table"), "tabla_inexistente"),
                              (("1054", "unknown column"), "columna_inexistente"),
                              (("1055", "group by", "aggregate"), "agregacion_incorrecta")]:
        if any(word in text for word in needles):
            return category
    if error:
        return "error_ejecucion"
    differences = structural_differences(reference_sql, generated_sql)
    return differences[0] if len(differences) == 1 else "resultado_diferente"


def evaluate(examples, generate, executor_factory, *, model="baseline", strategy="directa",
             time_limit=30.0, clock=perf_counter):
    """execute gold and returned SQL outside the three generation callback calls.

    Reference failures abort the experiment: invalid gold must not lower EX.
    The function records elapsed time; it cannot forcibly cancel GPU kernels.
    """
    if strategy not in {"directa", "callback"}:
        raise ValueError("Estrategia desconocida")
    output = []
    for example in examples:
        execute = executor_factory(example["schema_id"])
        reference = execute(example["sql"])
        if not reference.get("ok"):
            if hasattr(execute, "close"):
                execute.close()
            raise RuntimeError(f"Referencia no ejecutable {example['id']}: {reference.get('error')}")
        calls, failures = [], []

        def callback(sql):
            calls.append(sql)
            if len(calls) > 3:
                raise RuntimeError("Límite de tres llamadas excedido")
            result = execute(sql)
            if not result.get("ok"):
                failures.append(result.get("error"))
            return {**result, "filas": result.get("filas", [])[:10]}

        start = clock()
        error, generated = "", ""
        try:
            generated = generate(example["esquema"], example["pregunta"],
                                 ejecutar=callback if strategy == "callback" else None)
            if not isinstance(generated, str):
                raise TypeError("generar_sql debe devolver str")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        elapsed = clock() - start
        actual = execute(generated) if generated and not error else {
            "ok": False, "columnas": [], "filas": [], "error": error}
        error = error or actual.get("error") or ""
        eligible = elapsed <= time_limit and len(calls) <= 3
        correct = eligible and compare_results(reference, actual, example.get("orden_importa", example.get("requiere_orden", False)))
        category = "" if correct else ("limite_excedido" if not eligible else
                    error_category(error, example["sql"], generated))
        output.append({"id": example["id"], "schema_id": example["schema_id"],
                       "dificultad": example["dificultad"], "pregunta": example["pregunta"],
                       "esquema": example["esquema"], "modelo": model, "estrategia": strategy,
                       "sql_referencia": example["sql"], "sql_generado": generated,
                       "ejecucion_ok": bool(actual.get("ok")), "resultado_correcto": bool(correct),
                       "latencia_segundos": elapsed, "llamadas_ejecutar": len(calls),
                       "consultas_callback": json.dumps(calls, ensure_ascii=False),
                       "errores_ejecutar": json.dumps(failures, ensure_ascii=False),
                       "errores_callback": len(failures), "limite_cumplido": eligible,
                       "categoria_error": category, "error": error,
                       "revision_humana": not correct and not bool(error) and eligible,
                       "resultado_observado": json.dumps(actual, ensure_ascii=False, default=str),
                       "causa_probable": ("Hipótesis por diferencia AST; requiere revisión humana: " + category)
                       if not correct and not error and eligible else category,
                       "mejora_sugerida": "Revisar pregunta, JOIN, filtros y agregaciones" if not correct else ""})
        if hasattr(execute, "close"):
            execute.close()
    return output


def grouped_summary(records):
    """One observed summary for each model, strategy and difficulty."""
    groups = defaultdict(list)
    for record in records:
        groups[(record["modelo"], record["estrategia"], record["dificultad"])].append(record)
    output = []
    for (model, strategy, difficulty), group in sorted(groups.items()):
        output.append({"modelo": model, "estrategia": strategy, "dificultad": difficulty,
                       **summarize(group), "errores": sum(not r["resultado_correcto"] for r in group)})
    return output


def summarize(records):
    if not records:
        raise ValueError("Evaluación vacía")
    return {"preguntas": len(records), "ex_ponderada": weighted_ex(records),
            "latencia_promedio": sum(r["latencia_segundos"] for r in records) / len(records),
            "latencia_maxima": max(r["latencia_segundos"] for r in records),
            "fuera_de_limite": sum(not r["limite_cumplido"] for r in records),
            "llamadas_ejecutar": sum(r["llamadas_ejecutar"] for r in records),
            "reparaciones_exitosas": sum(r["errores_callback"] > 0 and r["resultado_correcto"] for r in records),
            "reparaciones_fallidas": sum(r["errores_callback"] > 0 and not r["resultado_correcto"] for r in records)}


def write_csv(path, records, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def write_reports(records, directory, filename="baseline.csv"):
    path = Path(directory)
    write_csv(path / filename, records)
    write_csv(path / "errores.csv", [r for r in records if not r["resultado_correcto"]], list(records[0]))
    summary = summarize(records)
    write_csv(path / (Path(filename).stem + "_por_dificultad.csv"), grouped_summary(records))
    (path / (Path(filename).stem + "_resumen.json")).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary
