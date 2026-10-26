"""Pruebas de integración reales separadas de los tests con mocks."""
import json
from pathlib import Path
from time import perf_counter
from scripts.with_env import load_env
from src.data.mysql import MySQLExecutor

def main():
    load_env()
    rows=[]
    cases={
        'join': 'SELECT c.id, m.id FROM consultas c JOIN medicos m ON c.medico_id=m.id',
        'group_having':'SELECT medico_id, COUNT(*) AS total FROM consultas GROUP BY medico_id HAVING COUNT(*)>=1',
        'subconsulta':'SELECT id FROM consultas WHERE costo > (SELECT AVG(costo) FROM consultas)',
        'cte':'WITH total AS (SELECT COUNT(*) AS n FROM consultas) SELECT n FROM total',
        'ventana':'SELECT id, ROW_NUMBER() OVER (ORDER BY costo, id) AS n FROM consultas',
        'fecha':'SELECT YEAR(fecha), COUNT(*) FROM consultas GROUP BY YEAR(fecha)',
    }
    with MySQLExecutor('hospital') as database:
        for name,sql in cases.items():
            start=perf_counter();result=database(sql)
            rows.append({'prueba':name,'ok':result['ok'],'filas':len(result['filas']),'segundos':perf_counter()-start,'error':result['error']})
        invalid=database('SELECT id, COUNT(*) FROM consultas')
        rows.append({'prueba':'only_full_group_by_rechaza','ok':not invalid['ok'] and invalid.get('errno')==1140,'error':invalid['error']})
        # Verificar defensa de permisos directamente sin el filtro AST, sin escritura efectiva.
        cursor=database.connection.cursor()
        try:
            cursor.execute('DELETE FROM consultas WHERE 1=0')
            rows.append({'prueba':'permisos_delete_rechazan','ok':False})
        except Exception as exc:
            rows.append({'prueba':'permisos_delete_rechazan','ok':getattr(exc,'errno',None)==1142,'errno':getattr(exc,'errno',None)})
        finally:
            database.connection.rollback();cursor.close()
    report={'motor':'MySQL 8.4.10','pruebas':rows,'aprobadas':sum(r['ok'] for r in rows),'fallidas':sum(not r['ok'] for r in rows)}
    Path('resultados/metricas/mysql_integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if report['fallidas']: raise SystemExit(1)

if __name__=='__main__':main()
