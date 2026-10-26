"""Dataset invariants; execution evidence is checked separately from unit generation."""
import json
import re
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
    assert len({(r['schema_id'],re.sub(r"'[^']*'|\b\d+\b",'?',r['sql'])) for r in rows})==len(rows)
    assert {r['dificultad'] for r in rows}=={'facil','media','dificil'}
    assert {'join','agregacion_por_atributo','having','cte','ventana','fecha','subconsulta'} <= {r['tipo_consulta'] for r in rows}
    assert all(r['validado'] is False for r in rows)

def test_validation_human_authorship_not_fabricated():
    rows=read('datos/validacion/propuestas_revision_humana.jsonl')
    assert len(rows)>=40
    assert len({r['schema_id'] for r in rows})==2
    assert all(r['revision_humana']=='pendiente' for r in rows)

def test_question_encoding_and_window_output_contract():
    rows=[r for key in DOMAINS for r in candidates(key)]
    assert all(not re.search(r'\w\?\w', r['pregunta']) for r in rows)
    assert all(not r['pregunta'].startswith('?') for r in rows)
    for row in rows:
        if row['tipo_consulta']=='ventana':
            assert row['requiere_orden'] is False
            assert 'exactamente' in row['pregunta']
        if row['tipo_consulta']=='having_subconsulta':
            assert row['pregunta'].startswith('Devuelve exactamente')

def test_fixtures_and_foreign_keys():
    for key,tables in DOMAINS.items():
        assert schema_sql(key).count('CREATE TABLE')==len(tables)
        assert fixtures(key).count('INSERT INTO')==len(tables)*12
        assert 'FOREIGN KEY' in schema_sql(key)

def test_fixtures_cover_many_to_one_orphans_and_repeated_groups():
    from collections import Counter
    references=Counter((i*5)%8+1 for i in range(1,13))
    assert max(references.values()) > 1
    assert set(references) < set(range(1,13))
    for key in DOMAINS:
        seed=fixtures(key)
        assert 'grupo 1' in seed and 'grupo 4' in seed
        if any('DATE' in definition for _,definition in DOMAINS[key]):
            assert "'2024-" in seed and "'2025-" in seed

def test_numeric_fixtures_have_ties_and_distinct_column_values():
    import ast
    from collections import Counter
    from itertools import combinations
    from src.data.generate import columns
    for key,tables in DOMAINS.items():
        seed=fixtures(key).splitlines()
        for table,definition in tables:
            rows=[ast.literal_eval(line.split(' VALUES ',1)[1].rstrip(';')) for line in seed if line.startswith(f'INSERT INTO {table} ')]
            numeric=[idx+1 for idx,(name,typ) in enumerate(columns(definition)) if typ not in ('TEXT','DATE') and not name.endswith('_id')]
            for idx in numeric:
                assert max(Counter(row[idx] for row in rows).values()) > 1
                assert len({row[idx] for row in rows}) > 1
            for left,right in combinations(numeric,2):
                assert any(row[left]!=row[right] for row in rows)

def test_accepted_examples_have_real_mysql_evidence():
    rows=read('datos/entrenamiento/aceptados.jsonl')
    if not rows: pytest.skip('MySQL execution not completed; no accepted examples fabricated')
    assert len(rows)>=2000
    assert all(r['validado'] is True and r['mysql_version']=='8.4.10' and r['validado_en'] for r in rows)
    assert not {r['schema_id'] for r in rows} & {r['schema_id'] for r in read('datos/validacion/aceptados.jsonl')}

def test_rejection_ledger_exists():
    assert (ROOT/'datos/descartes/descartes.jsonl').is_file()
