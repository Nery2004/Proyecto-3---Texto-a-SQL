"""Read-only mathematical oracle derived from Spanish questions, never gold SQL."""
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.evaluation.metrics import compare_results


@dataclass(frozen=True)
class Specification:
    table: str
    metric: str
    operation: str
    group: str | None = None
    having_global_average: bool = False


def parse_question(question):
    """Recognize only the documented question grammar; return None otherwise."""
    text=''.join(c for c in unicodedata.normalize('NFD',question)
                 if unicodedata.category(c)!='Mn')
    token=r'([a-z_][a-z_0-9]*)'
    operations={'promedio':'avg','suma':'sum','maximo':'max','minimo':'min'}
    m=re.fullmatch(r'Devuelve exactamente '+token+r' y el (promedio|suma|maximo|minimo) de '+token+r', una fila por cada valor distinto de '+token+r' en '+token+r'\.',text)
    if m:
        group,operation,metric,repeated,table=m.groups()
        if group!=repeated: raise ValueError('Grupos contradictorios en pregunta')
        return Specification(table,metric,operations[operation],group)
    m=re.fullmatch(r'Devuelve exactamente '+token+r' y el (promedio|suma|maximo|minimo) de '+token+r' para los grupos de '+token+r' cuyo (promedio|suma|maximo|minimo) de '+token+r' supera el promedio global de '+token+r' de toda la tabla\.',text)
    if m:
        group,operation,metric,table,repeated_operation,repeated_metric,global_metric=m.groups()
        if operation!=repeated_operation or len({metric,repeated_metric,global_metric})!=1:
            raise ValueError('Agregados contradictorios en pregunta')
        return Specification(table,metric,operations[operation],group,True)
    families=[
        (r'la cantidad de valores distintos de ','count_distinct'),
        (r'la diferencia entre maximo y minimo de ','range'),
        (r'la desviacion estandar poblacional de ','stddev_pop'),
    ]
    for phrase,operation in families:
        m=re.fullmatch(r'Devuelve exactamente '+token+r' y '+phrase+token+r', una fila por cada '+token+r' en '+token+r'\.',text)
        if m:
            group,metric,repeated,table=m.groups()
            if group!=repeated: raise ValueError('Grupos contradictorios en pregunta')
            return Specification(table,metric,operation,group)
    m=re.fullmatch(r'Muestra exactamente id, '+token+r' y un rango global de '+token+r' calculado por '+token+r' descendente: los empates comparten rango y no se dejan saltos entre rangos\. No dividas los registros en grupos\.',text)
    if m:
        metric,table,repeated=m.groups()
        if metric!=repeated: raise ValueError('Orden contradictorio en pregunta')
        return Specification(table,metric,'dense_rank')
    return None


def aggregate(values,operation):
    values=[Decimal(str(v)) for v in values if v is not None]
    if operation=='count_distinct': return len(set(values))
    if not values: return None
    with localcontext() as ctx:
        ctx.prec=50
        if operation=='sum': return sum(values,Decimal(0))
        if operation=='avg': return sum(values,Decimal(0))/len(values)
        if operation=='min': return min(values)
        if operation=='max': return max(values)
        if operation=='range': return max(values)-min(values)
        if operation=='stddev_pop':
            mean=sum(values,Decimal(0))/len(values)
            return (sum(((v-mean)**2 for v in values),Decimal(0))/len(values)).sqrt()
    raise ValueError(f'Operación desconocida: {operation}')


def expected_result(specification,records):
    s=specification
    if s.operation=='dense_rank':
        distinct=sorted({r[s.metric] for r in records if r[s.metric] is not None},reverse=True)
        ranks={value:i+1 for i,value in enumerate(distinct)}
        rows=[(r['id'],r[s.metric],ranks.get(r[s.metric],len(distinct)+1)) for r in records]
        return {'ok':True,'columnas':['id',s.metric,'rango'],'filas':rows}
    groups=defaultdict(list)
    for row in records: groups[row[s.group]].append(row[s.metric])
    global_average=aggregate([r[s.metric] for r in records],'avg')
    rows=[]
    for key,values in groups.items():
        value=aggregate(values,s.operation)
        if s.having_global_average and (value is None or global_average is None or value<=global_average):
            continue
        rows.append((key,value))
    return {'ok':True,'columnas':[s.group,'valor'],'filas':rows}


def audit(root,output):
    from src.data.mysql import MySQLExecutor
    from src.data.generate import DOMAINS
    paths=[root/'datos/entrenamiento/aceptados.jsonl',root/'datos/validacion/aceptados.jsonl']
    original_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    rows=[json.loads(line) for path in paths for line in path.read_text(encoding='utf-8').splitlines()]
    details=[]; negative_controls=[]; cache={}; counts=Counter(); families=Counter()
    executor=None;current=None;controlled=set()
    try:
        for row in rows:
            specification=parse_question(row['pregunta'])
            if specification is None:
                counts['no_aplica']+=1
                continue
            s=specification
            if s.table not in {table for table,_ in DOMAINS[row['schema_id']]}:
                raise ValueError('Pregunta referencia una tabla fuera del esquema')
            if row['schema_id']!=current:
                if executor: executor.close()
                executor=MySQLExecutor(row['schema_id']);current=row['schema_id']
            key=(current,s.table)
            if key not in cache:
                actual_table=executor(f'SELECT * FROM `{s.table}`')
                if not actual_table['ok']: raise RuntimeError(actual_table['error'])
                cache[key]=[dict(zip(actual_table['columnas'],values)) for values in actual_table['filas']]
            reference=expected_result(s,cache[key])
            # Gold SQL is first consulted here, after the independent expected result.
            observed=executor(row['sql'])
            correct=compare_results(reference,observed,order_matters=False)
            families[s.operation+('_having' if s.having_global_average else '')]+=1
            counts['verificados' if correct else 'errores']+=1
            details.append({'id':row['id'],'schema_id':current,'familia':s.operation,'correcto':correct,'filas_esperadas':len(reference['filas']),'error_mysql':observed.get('error')})
            if current not in controlled and s.operation=='avg' and not s.having_global_average:
                wrong_sql=f'SELECT `{s.group}`, SUM(`{s.metric}`) FROM `{s.table}` GROUP BY `{s.group}`'
                wrong_result=executor(wrong_sql)
                detected=wrong_result['ok'] and not compare_results(reference,wrong_result)
                if detected:
                    controlled.add(current)
                    negative_controls.append({'schema_id':current,'id':row['id'],'mutacion':'SUM en lugar de AVG pedido por la pregunta','sql_incorrecto':wrong_sql,'ejecutable':True,'detectado':True})
    finally:
        if executor: executor.close()
    assert original_hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'Dataset cambió durante auditoría'
    report={'fecha_utc':datetime.now(timezone.utc).isoformat(),'motor':'MySQL 8.4.10','fuente_expected':'Pregunta en español interpretada mediante gramática regex; cálculo Python sobre SELECT *; no SQL de referencia','autoria':'Auditoría automática de Codex; no es revisión humana','datasets_sha256':original_hashes,'total':len(rows),'verificados':counts['verificados'],'no_aplica':counts['no_aplica'],'errores':counts['errores'],'familias':dict(families),'controles_negativos':negative_controls,'detalles':details}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('total','verificados','no_aplica','errores','familias')},ensure_ascii=False))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--output',type=Path,default=Path('resultados/metricas/semantic_oracle.json'))
    arguments=parser.parse_args()
    result=audit(arguments.root,arguments.output)
    sys.exit(1 if result['errores'] else 0)
