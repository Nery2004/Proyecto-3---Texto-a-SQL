"""Rubric comparator: bag semantics, two decimals and one extra column."""
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations
from numbers import Number
import unicodedata


def difficulty_weight(value):
    key = "".join(c for c in unicodedata.normalize("NFD", str(value).lower())
                  if unicodedata.category(c) != "Mn")
    return {"facil": 1, "media": 2, "medio": 2, "dificil": 3}[key]


def normalize(value):
    if isinstance(value, (Number, Decimal)) and not isinstance(value, (bool, complex)):
        decimal = Decimal(str(value))
        if decimal.is_finite():
            return decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if isinstance(value, (bytearray, memoryview)):
        return bytes(value)
    return value


def compare_results(expected, actual, order_matters=False):
    """Compare callback dictionaries; ignore aliases but preserve column order.

    Exactly one additional actual column may be dropped at any position. Empty
    results still require compatible column counts. Duplicate rows are retained.
    """
    if not expected.get("ok") or not actual.get("ok"):
        return False
    n = len(expected["columnas"])
    m = len(actual["columnas"])
    if m not in (n, n + 1):
        return False
    reference = [tuple(normalize(v) for v in row) for row in expected["filas"]]
    if any(len(row) != n for row in reference):
        return False
    rows = actual["filas"]
    if any(len(row) != m for row in rows):
        return False
    for positions in combinations(range(m), n):
        candidate = [tuple(normalize(row[i]) for i in positions) for row in rows]
        if (reference == candidate if order_matters else Counter(reference) == Counter(candidate)):
            return True
    return False


def weighted_ex(records):
    """Return weighted accuracy in [0, 1]; empty evaluation is undefined."""
    denominator = sum(difficulty_weight(row["dificultad"]) for row in records)
    if not denominator:
        raise ValueError("No hay preguntas para calcular EX")
    return sum(difficulty_weight(row["dificultad"]) for row in records
               if row["resultado_correcto"]) / denominator
