"""Defensa AST conservadora; siempre respaldar con usuario MySQL SELECT-only."""
import re
import sqlglot
from sqlglot import exp

class UnsafeSQL(ValueError):
    pass

def validate_sql(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise UnsafeSQL("SQL vacío")
    # MySQL ejecuta comentarios versionados aunque el parser los trate como comentarios.
    if re.search(r"/\*\s*[!+]", sql):
        raise UnsafeSQL("Comentarios ejecutables/hints no permitidos")
    try:
        trees = sqlglot.parse(sql, read="mysql")
    except sqlglot.errors.ParseError as exc:
        raise UnsafeSQL(str(exc)) from exc
    if len(trees) != 1 or trees[0] is None or not isinstance(trees[0], (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise UnsafeSQL("Se requiere una única consulta SELECT")
    tree = trees[0]
    forbidden = {"Insert", "Update", "Delete", "Drop", "Alter", "Create", "Command", "Into", "Lock", "Transaction", "Set", "Merge", "Grant", "Revoke", "Copy", "Use", "Placeholder", "Parameter"}
    dangerous = {"SLEEP", "BENCHMARK", "LOAD_FILE", "GET_LOCK", "RELEASE_LOCK", "RELEASE_ALL_LOCKS", "IS_FREE_LOCK", "IS_USED_LOCK", "SYS_EXEC", "SYS_EVAL", "MASTER_POS_WAIT", "SOURCE_POS_WAIT"}
    for node in tree.walk():
        if type(node).__name__ in forbidden:
            raise UnsafeSQL(f"Operación no permitida: {type(node).__name__}")
        if isinstance(node, exp.Func):
            name = node.name if isinstance(node, exp.Anonymous) else node.sql_name()
            if name.upper() in dangerous or isinstance(node.parent, exp.Dot):
                raise UnsafeSQL(f"Función no permitida: {name}")
    return tree.sql(dialect="mysql")

def clean_sql(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        match = re.fullmatch(r"```(?:sql|mysql)?\s*\n?(.*?)\n?```", text, re.S | re.I)
        if not match:
            raise UnsafeSQL("Bloque Markdown inválido")
        text = match.group(1).strip()
    return validate_sql(text)
