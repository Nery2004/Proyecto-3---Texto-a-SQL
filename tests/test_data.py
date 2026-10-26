"""Dataset invariants; execution evidence is checked separately from unit generation."""
import json
from pathlib import Path
import pytest
from src.data.generate import DOMAINS,candidates,schema_sql,fixtures
ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return [json.loads(x) for x in (ROOT/path).read_text(encoding='utf-8').splitlines() if x]

def test_ten_training_two_heldout_schemas():
    names=list(DOMAINS)
    assert len(names[:10])==10 and len(names[10:])==2
    assert not set(names[:10]) & set(names[10:])

def test_candidates_are_reproducible_and_diverse():
    rows=[r for key in list(DOMAINS)[:10] for r in candidates(key)]
    assert len(rows)>=2000
    assert len({(r['schema_id'],r['sql']) for r in rows})==len(rows)
    assert len({r['id'] for r in rows})==len(rows)
    assert {r['dificultad'] for r in rows}=={'facil','media','dificil'}
    assert {'join','group_by','having','cte','ventana','fecha','subconsulta'} <= {r['tipo_consulta'] for r in rows}
    assert all(r['validado'] is False for r in rows)

def test_validation_human_authorship_not_fabricated():
    rows=read('datos/validacion/propuestas_revision_humana.jsonl')
    assert len(rows)>=40
    assert len({r['schema_id'] for r in rows})==2
    assert all(r['revision_humana']=='pendiente' for r in rows)

def test_fixtures_and_foreign_keys():
    for key,tables in DOMAINS.items():
        assert schema_sql(key).count('CREATE TABLE')==len(tables)
        assert fixtures(key).count('INSERT INTO')==len(tables)*12
        assert 'FOREIGN KEY' in schema_sql(key)

def test_accepted_examples_have_real_mysql_evidence():
    rows=read('datos/entrenamiento/aceptados.jsonl')
    if not rows: pytest.skip('MySQL execution not completed; no accepted examples fabricated')
    assert len(rows)>=2000
    assert all(r['validado'] is True and r['mysql_version']=='8.4.10' and r['validado_en'] for r in rows)
    assert not {r['schema_id'] for r in rows} & {r['schema_id'] for r in read('datos/validacion/aceptados.jsonl')}

def test_rejection_ledger_exists():
    assert (ROOT/'datos/descartes/descartes.jsonl').is_file()
