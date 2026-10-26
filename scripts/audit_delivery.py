"""Audita artefactos sin convertir pendientes externos en pruebas aprobadas."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',default='resultados/metricas/auditoria_entrega.json')
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args();checks=[]
    def record(name,ok,detail):checks.append({'requisito':name,'estado':'PASS' if ok else 'PENDIENTE','detalle':detail})
    def read(path):
        p=Path(path)
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    train=[json.loads(s) for s in Path('datos/entrenamiento/aceptados.jsonl').read_text(encoding='utf-8').splitlines()]
    valid=[json.loads(s) for s in Path('datos/validacion/aceptados.jsonl').read_text(encoding='utf-8').splitlines()]
    record('2000_train_mysql',len(train)>=2000 and all(r.get('validado') and r.get('mysql_version')=='8.4.10' for r in train),len(train))
    record('10_esquemas_train',len({r['schema_id'] for r in train})>=10,sorted({r['schema_id'] for r in train}))
    record('validacion_independiente',len(valid)>=40 and len({r['schema_id'] for r in valid})>=2 and not {r['schema_id'] for r in valid}&{r['schema_id'] for r in train},len(valid))
    for name in 'ab':
        run=read(f'adapters_experimentos/config_{name}/run.json')
        record('entrenamiento_'+name,run.get('estado')=='completado' and run.get('pasos',0)>0,run.get('estado','sin registro final'))
    config=read('config.json')
    record('config_adapter_activo',config.get('usar_adapter') is True,config)
    weights=Path('adapter/adapter_model.safetensors')
    record('pesos_finales',weights.is_file() and weights.stat().st_size>0,str(weights))
    selection=read('resultados/seleccion_adapter.json')
    if weights.is_file():
        record('hash_adapter_elegido',hashlib.sha256(weights.read_bytes()).hexdigest()==selection.get('sha256_pesos'),selection.get('seleccion'))
    tests=read('resultados/metricas/pruebas.json')
    record('tests_unitarios',tests.get('aprobadas',0)>0 and tests.get('fallidas')==0,tests)
    integration=read('resultados/metricas/mysql_integration.json')
    record('tests_mysql_reales',integration.get('aprobadas')==8 and integration.get('fallidas')==0,integration.get('aprobadas'))
    for path in ['solucion.py','requirements.txt','README.md','BITACORA.md','CONTRIBUCIONES.md','historial_git.txt','presentacion.pdf','docs/analisis_errores.md','resultados/seleccion_adapter.json']:
        record(path,Path(path).is_file(),path)
    repo=read('docs/github_access.json')
    record('repositorio_privado',repo.get('after')=='private',repo.get('after'))
    tracked=subprocess.check_output(['git','ls-files'],text=True).splitlines()
    forbidden=[p for p in tracked if Path(p).name.startswith('.env') or any(x in Path(p).parts for x in ['.venv','.runtime','__pycache__','checkpoints'])]
    record('sin_archivos_privados_o_caches_seguidos',not forbidden,forbidden)
    # Estos requisitos dependen de evidencia externa o revisión humana real.
    record('colab_T4',False,'Solo GPU RTX4060 y arranque MySQL Linux verificados; T4 pendiente')
    record('autoria_validacion_estudiante',all(r.get('revision_humana') not in (None,'pendiente') for r in valid),'Propuestas IA; completar revisión/redacción verdadera')
    record('acceso_docente',False,'El usuario desconoce su usuario GitHub; no se afirma invitación')
    record('modalidad_pareja',False,'Usuario confirmó trabajo individual; sin segundo integrante ficticio')
    report={'estado_general':'PARCIAL' if any(c['estado']!='PASS' for c in checks) else 'COMPLETO',
            'aprobados':sum(c['estado']=='PASS' for c in checks),'pendientes':sum(c['estado']=='PENDIENTE' for c in checks),'checks':checks}
    if not args.check_only:
        Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
