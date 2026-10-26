"""Generate candidates, initialize MySQL, or record execution evidence."""
import argparse
from pathlib import Path
import json
import sys
from collections import Counter
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.data.generate import generate,write_jsonl

def validate(root):
    from src.data.mysql import MySQLExecutor
    summary={}
    rejected=[]
    for split,filename in [('entrenamiento','candidatos.jsonl'),('validacion','propuestas_revision_humana.jsonl')]:
        source=root/'datos'/split/filename
        records=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
        accepted=[]; seen=set(); executor=None; current=None
        try:
            for row in records:
                if current!=row['schema_id']:
                    if executor: executor.close()
                    executor=MySQLExecutor(row['schema_id']);current=row['schema_id']
                key=(current,' '.join(row['sql'].lower().split()))
                result={'ok':False,'error':'Consulta duplicada','errno':None} if key in seen else executor(row['sql'])
                seen.add(key)
                now=datetime.now(timezone.utc).isoformat()
                if result['ok']:
                    row.update(validado=True,mysql_version=executor.version.split('-')[0],validacion_motor='MySQL',validado_en=now,filas_referencia=len(result['filas']),revision_semantica='pendiente humana')
                    accepted.append(row)
                else:
                    errno=result.get('errno')
                    reason={1064:'sintaxis_invalida',1146:'tabla_inexistente',1054:'columna_inexistente',1055:'only_full_group_by'}.get(errno,'duplicado' if key in seen and result['error']=='Consulta duplicada' else 'error_ejecucion')
                    rejected.append({'id':row['id'],'schema_id':current,'sql':row['sql'],'motivo':reason,'detalle_error':result['error'],'fecha':now})
        finally:
            if executor: executor.close()
        write_jsonl(root/'datos'/split/'aceptados.jsonl',accepted)
        summary[split]={'propuestos':len(records),'aceptados':len(accepted),'descartados':len(records)-len(accepted),'por_dificultad':dict(Counter(r['dificultad'] for r in accepted)),'por_esquema':dict(Counter(r['schema_id'] for r in accepted)),'por_tipo_consulta':dict(Counter(r['tipo_consulta'] for r in accepted))}
    write_jsonl(root/'datos/descartes/descartes.jsonl',rejected)
    summary['descartes_por_motivo']=dict(Counter(r['motivo'] for r in rejected))
    summary['revision_semantica_humana']='pendiente; ejecución correcta no prueba equivalencia semántica'
    (root/'datos/fuentes/estadisticas.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['generate','initialize','validate'])
    parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--reset-owned',action='store_true',help='Rebuild only the 12 allowlisted textsql_<domain> fixture databases')
    args=parser.parse_args()
    if args.action=='generate': print(generate(args.root))
    elif args.action=='initialize':
        from src.data.mysql import initialize
        initialize(reset_owned=args.reset_owned)
    else: validate(args.root)
