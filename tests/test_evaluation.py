from decimal import Decimal
import pytest
from src.evaluation import compare_results, weighted_ex, evaluate, summarize
from src.evaluation.runner import error_category, grouped_summary, write_reports


def result(rows, columns=("x",)):
    return {"ok": True, "columnas": columns, "filas": rows, "error": None}


def test_weighted_ex():
    assert weighted_ex([{"dificultad": "fácil", "resultado_correcto": True},
                        {"dificultad": "media", "resultado_correcto": False},
                        {"dificultad": "difícil", "resultado_correcto": True}]) == 4 / 6
    with pytest.raises(ValueError):
        weighted_ex([])


def test_rounding_and_order():
    assert compare_results(result([(Decimal("1.234"),), (2,)]), result([(2.0,), (1.23,)]))
    assert not compare_results(result([(1,), (2,)]), result([(2,), (1,)]), True)
    assert compare_results(result([(1.235,)]), result([(1.24,)]))


def test_extra_column_and_duplicates():
    assert compare_results(result([(1,), (1,)]), result([("a", 1), ("b", 1)], ("extra", "x")))
    assert not compare_results(result([(1,), (1,)]), result([(1,)]))
    assert not compare_results(result([]), result([], ("a", "b", "c")))
    assert compare_results(result([(None,), ("1",)]), result([("1",), (None,)]))
    assert not compare_results(result([(1,)]), result([("1",)]))


EXAMPLE = {"id": "x", "schema_id": "schema", "esquema": "CREATE TABLE x (a INT)",
           "pregunta": "Uno", "sql": "SELECT 1", "dificultad": "facil"}


def test_execution_comparison_and_budget():
    execute = lambda sql: result([(1,)])
    def generate(schema, question, ejecutar=None):
        for _ in range(4):
            ejecutar("SELECT 1")
        return "SELECT 1"
    records = evaluate([EXAMPLE], generate, lambda schema: execute, strategy="callback")
    assert not records[0]["resultado_correcto"]
    assert records[0]["llamadas_ejecutar"] == 4
    assert records[0]["categoria_error"] == "limite_excedido"


def test_latency_excludes_over_limit_success():
    clock_values = iter([0.0, 30.01])
    records = evaluate([EXAMPLE], lambda *a, **k: "SELECT 1",
                       lambda schema: lambda sql: result([(1,)]), clock=lambda: next(clock_values))
    assert records[0]["ejecucion_ok"]
    assert not records[0]["resultado_correcto"]
    assert summarize(records)["ex_ponderada"] == 0


def test_reference_failure_aborts():
    with pytest.raises(RuntimeError, match="Referencia"):
        evaluate([EXAMPLE], lambda *a, **k: "SELECT 1",
                 lambda schema: lambda sql: {"ok": False, "error": "missing db"})


@pytest.mark.parametrize("gold,sql,category", [
    ("SELECT a FROM t JOIN u ON t.id=u.id", "SELECT a FROM t", "join_incorrecto"),
    ("SELECT SUM(a) FROM t", "SELECT AVG(a) FROM t", "agregacion_incorrecta"),
    ("SELECT a FROM t WHERE a=1", "SELECT a FROM t WHERE a=2", "filtro_incorrecto"),
    ("SELECT SUM(a) FROM t WHERE a=1", "SELECT a FROM t WHERE a=2", "resultado_diferente"),
])
def test_structural_categories_are_hypotheses(gold, sql, category):
    assert error_category("", gold, sql) == category


def test_callback_preview_does_not_truncate_scoring():
    rows = [(i,) for i in range(15)]
    def generate(schema, question, ejecutar=None):
        assert len(ejecutar("SELECT a FROM x")["filas"]) == 10
        return "SELECT a FROM x"
    records = evaluate([EXAMPLE], generate, lambda schema: lambda sql: result(rows), strategy="callback")
    assert records[0]["resultado_correcto"]
    assert "14" in records[0]["resultado_observado"]


def test_grouped_report_and_encoding(tmp_path):
    records = evaluate([EXAMPLE], lambda *a, **k: "SELECT 1",
                       lambda schema: lambda sql: result([(1,)]))
    groups = grouped_summary(records)
    assert groups[0]["modelo"] == "baseline"
    assert groups[0]["dificultad"] == "facil"
    assert groups[0]["ex_ponderada"] == 1
    assert groups[0]["errores"] == 0
    write_reports(records, tmp_path)
    assert (tmp_path / "baseline_por_dificultad.csv").is_file()
    from pathlib import Path
    for path in [*Path("src/evaluation").glob("*.py"), Path("scripts/evaluate.py")]:
        source = path.read_text(encoding="utf-8")
        assert "\u00c3\u00ad" not in source
        assert "\ufffd" not in source
