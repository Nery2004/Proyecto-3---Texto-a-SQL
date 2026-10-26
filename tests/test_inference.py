import inspect
import time
import pytest
import solucion
from src.inference import engine
from src.inference.safety import validate_sql, clean_sql, UnsafeSQL
from src.inference.prompt import messages

@pytest.mark.parametrize("sql", ["INSERT INTO a VALUES(1)", "UPDATE a SET x=1", "DELETE FROM a", "DROP TABLE a", "SELECT 1; SELECT 2", "SELECT * FROM a INTO OUTFILE '/tmp/a'", "SELECT SLEEP(3)", "SELECT (SELECT LOAD_FILE('/etc/passwd'))", "SELECT 1 /*! INTO OUTFILE '/tmp/a' */", "SELECT GET_LOCK('a',1)", "SELECT @x := 1"])
def test_unsafe(sql):
    with pytest.raises((UnsafeSQL, ValueError)):
        validate_sql(sql)

@pytest.mark.parametrize("sql", ["SELECT a.id FROM a JOIN b ON a.id=b.id", "SELECT x, COUNT(*) FROM a GROUP BY x HAVING COUNT(*)>1", "WITH a AS (SELECT 1 x) SELECT x FROM a", "SELECT ROW_NUMBER() OVER (ORDER BY x) FROM a", "SELECT * FROM a WHERE d > DATE_SUB(CURDATE(), INTERVAL 2 DAY)"])
def test_readonly(sql):
    assert isinstance(validate_sql(sql), str)

def test_contract():
    assert str(inspect.signature(solucion.generar_sql)) == "(esquema: str, pregunta: str, ejecutar=None) -> str"
    assert clean_sql("```sql\nSELECT 1;\n```") == "SELECT 1"

def test_callback_limit(monkeypatch):
    class Fake:
        def generate(self, *args): return "SELECT 1"
    monkeypatch.setattr(engine, "get_runtime", lambda: Fake())
    calls=[]
    assert solucion.generar_sql("", "uno", lambda q: calls.append(q) or {"ok":False,"error":"fallo"}) == "SELECT 1"
    assert len(calls)==3
    assert solucion.generar_sql("", "uno") == solucion.generar_sql("", "uno")

def test_bad_candidate_never_executed(monkeypatch):
    class Fake:
        def generate(self,*args): return "DELETE FROM a"
    monkeypatch.setattr(engine,"get_runtime",lambda:Fake())
    with pytest.raises(UnsafeSQL):
        solucion.generar_sql("", "uno", lambda _: pytest.fail("unsafe callback"))

def test_same_prompt():
    assert messages("CREATE TABLE a(x INT)","uno") == messages("CREATE TABLE a(x INT)","uno")
