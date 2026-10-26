"""Genera presentación y estado usando únicamente evidencia existente."""
import argparse
import csv
import textwrap
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

def read_json(path, default=None):
    p=Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def measured_rows():
    path=Path('resultados/resumen_comparacion.csv')
    rows=list(csv.DictReader(path.open(encoding='utf-8'))) if path.exists() else []
    if not rows:
        summary=read_json('resultados/baseline_resumen.json')
        if summary: rows=[dict(summary,modelo='baseline',estrategia='directa')]
    return rows


def metric_line(row):
    return (f"{row['modelo']}/{row['estrategia']}: EX {float(row['ex_ponderada']):.4f}; "
            f"n={row['preguntas']}; media {float(row['latencia_promedio']):.2f}s; "
            f"máx {float(row['latencia_maxima']):.2f}s; fuera límite {row['fuera_de_limite']}")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status-only',action='store_true',help='Actualizar estado provisional sin reemplazar PDF')
    args=parser.parse_args()
    measured=measured_rows()
    selection=read_json('resultados/seleccion_adapter.json',{})
    analysis=read_json('resultados/metricas/analisis_errores.json',{})
    gpu=read_json('resultados/metricas/imports_gpu.json',{})
    choice=selection.get('seleccion',{})
    chosen=analysis.get(f"inference_{choice.get('experimento')}/callback",{})
    domains=chosen.get('ex_por_esquema',{})
    prediction=(f"EX observada {chosen['ex']:.4f}; predicción heurística {min(domains.values()):.2f}: mínimo entre dominios; EX oculta desconocida."
                if domains else 'Predicción pendiente de selección y análisis medidos; EX oculta desconocida.')
    training_lines=[]
    stats=read_json('datos/fuentes/estadisticas.json',{})
    train=stats.get('entrenamiento',{});valid=stats.get('validacion',{})
    load=read_json('resultados/metricas/carga_baseline.json',{'estado':'pendiente'})
    unit=read_json('resultados/metricas/pruebas.json',{})
    integration=read_json('resultados/metricas/mysql_integration.json',{})
    runs={name:read_json(f'adapters_experimentos/config_{name}/run.json',read_json(f'adapters_experimentos/config_{name}/progreso.json',{'estado':'no ejecutado'})) for name in 'ab'}
    summary=read_json('resultados/baseline_resumen.json')
    ex=str(summary['ex_ponderada']) if summary else 'Pendiente: no se ha medido EX'
    Path('resultados').mkdir(exist_ok=True)
    for filename in ['validacion_propia.csv','baseline.csv','comparacion_lora.csv','errores.csv']:
        path=Path('resultados')/filename
        if not path.exists():
            with path.open('w',newline='',encoding='utf-8') as stream:
                csv.writer(stream).writerow(['id','schema_id','dificultad','pregunta','sql_referencia','sql_generado','ejecucion_ok','resultado_correcto','latencia_segundos','categoria_error'])
    Path('resultados/README.md').write_text(
        '# Evidencia de ejecución\n\nLos CSV que solo tienen cabecera no contienen experimentos medidos.\n'
        'No implican EX=0. Los informes JSON registran intentos y errores reales.\n'
        'Las curvas de loss solo se crean tras pasos reales del entrenador.\n',encoding='utf-8')
    for name,run in runs.items():
        metrics=run.get('metricas',{})
        line=f"LoRA {name.upper()}: {run['estado']}; pasos {run.get('pasos','no registrados')}; tiempo {run.get('segundos','no registrado')}s"
        if 'train_loss' in metrics:line+=f"; loss {metrics['train_loss']:.4f}"
        training_lines.append(line)
    choice_line=(f"Adapter elegido: {choice['experimento'].upper()}; EX callback {choice['ex_callback']:.4f}" if choice else 'Adapter final pendiente de selección medida')
    phase=[('Inicialización y Git','Implementado; privacidad verificada, acceso docente pendiente'),
           ('Dataset',f"{train.get('aceptados',0)} aceptados MySQL; revisión semántica pendiente"),
           ('Validación',f"{valid.get('aceptados',0)} propuestas ejecutadas; autoría humana pendiente"),
           ('Resultados medidos','<br>'.join(metric_line(r) for r in measured) or 'Pendientes'),('QLoRA A',training_lines[0]),('QLoRA B',training_lines[1]),('Selección',choice_line),
           ('Inferencia',f"GPU medida: {gpu.get('gpu','pendiente')}; T4 no verificada"),
           ('Experimento y errores','Pipeline implementado; resultados dependen de ejecución real'),
           ('Pruebas',f"Unitarias: {unit}; integración MySQL: {integration.get('aprobadas',0)} aprobadas"),
           ('Colaboración','Trabajo individual confirmado por el estudiante; asistencia de Codex declarada')]
    text='# Estado real de ejecución\n\n**Estado general: PARCIAL.** Persisten requisitos humanos y verificación Colab T4.\n\n'
    text+='| Fase | Evidencia/estado |\n|---|---|\n'+''.join(f'| {a} | {b} |\n' for a,b in phase)
    text+='\n## Carga real del modelo\n\n```json\n'+json.dumps(load,ensure_ascii=False,indent=2)+'\n```\n'
    text+='\n## Pendientes obligatorios\n\nRevisar semántica y redacción/autoría estudiantil de las propuestas IA; verificar ejecución y rendimiento Colab T4; acceso docente pendiente (el estudiante desconoce su usuario GitHub); entrega Canvas. Entrenamientos, evaluaciones y selección siguen pendientes si falta su evidencia medida arriba. Trabajo individual declarado: no se atribuyen aportes a otro integrante.\n'
    text+='\n## Predicción y límites\n\n'+prediction+'\n\nDos dominios sintéticos y selección sobre la misma validación pueden sobreestimar generalización. El mínimo por dominio no es límite inferior ni intervalo de confianza.\n'
    Path('docs/estado_ejecucion.md').write_text(text,encoding='utf-8')
    slides=[
      ('Proyecto 3: Texto a SQL',['Universidad del Valle de Guatemala | Deep Learning 2026','Profesor: Kevin Recinos','25 de octubre de 2026','Estado PARCIAL: ver evidencia, sin métricas inventadas']),
      ('Objetivo y contrato',['DDL MySQL con comentarios + pregunta en español','solucion.generar_sql(esquema, pregunta, ejecutar=None) -> str','Una consulta SELECT o WITH ... SELECT','Carga <=300s; pregunta <=30s; callback <=3 llamadas']),
      ('Arquitectura',['Prompt compartido -> Qwen local -> limpieza -> validación AST','Modelo diferido/cacheado; NF4 GPU; generación greedy','Callback opcional: ejecutar y corregir errores','Usuario SELECT-only y transacción READ ONLY']),
      ('Modelo y datos',['Qwen/Qwen2.5-Coder-1.5B-Instruct',f"{train.get('aceptados',0)} pares aceptados: ejecución MySQL 8.4.10",'Diez esquemas propios; deduplicación normalizando literales',f"Descartados: {train.get('descartados',0)}; revisión semántica pendiente"]),
      ('Validación independiente',['Hotelería y manufactura: dominios ausentes en entrenamiento',f"{valid.get('aceptados',0)} propuestas ejecutadas; 48 fijadas para comparación",'Fácil/media/difícil; partición por esquema','Propuestas IA: revisión/redacción humana pendiente']),
      ('Baseline medido',[metric_line(r) for r in measured if r['modelo']=='baseline'] or ['Baseline pendiente']),
      ('Comparación LoRA',[metric_line(r) for r in measured if r['modelo']!='baseline']+[choice_line,'Mismo prompt y semilla; mejora no garantizada; EX oculta desconocida']),
      ('Dos configuraciones QLoRA',['Único factor: rank 8 frente a 16','Alpha16; dropout0.05; LR2e-4; 3 épocas; batch efectivo16','NF4 doble cuantización FP16; gradient checkpointing','Loss solo respuesta SQL; no se entrena con validación']),
      ('Entrenamiento y curvas',training_lines+['Curvas loss reales si existen; parámetros, pasos y VRAM en run.json']),
      ('Experimento de inferencia',[f"{r['modelo']}: reparadas {r['reparaciones_exitosas']}; fallidas {r['reparaciones_fallidas']}; llamadas {r['llamadas_ejecutar']}" for r in measured if r['estrategia']=='callback']+['EX pesos1/2/3; fuera de 30s o más de tres llamadas no cuenta éxito']),
      ('Pruebas, errores y predicción',[f'Pruebas unitarias: {unit}',f"Integración MySQL: {integration.get('aprobadas',0)} PASS"]+[f"{key}: "+', '.join(f'{category}={count}' for category,count in value.get('errores_por_categoria',{}).items()) for key,value in analysis.items()]+[prediction,'Causas AST requieren revisión humana; dos dominios sintéticos limitan generalización']),
      ('Entrega y pendientes',[choice_line,'Acceso docente pendiente: usuario GitHub desconocido','Trabajo individual; propuestas IA requieren revisión humana',f"GPU medida: {gpu.get('gpu','pendiente')}; T4 no verificada",'Uso de Codex declarado; verificar entrega académica'])]
    if args.status_only:
        print('Estado provisional actualizado; PDF conservado')
        return
    c=canvas.Canvas('presentacion.pdf',pagesize=(960,540))
    for i,(title,bullets) in enumerate(slides,1):
        c.setFillColor(HexColor('#101b30'));c.rect(0,0,960,540,fill=1,stroke=0)
        c.setFillColor(HexColor('#69d6c5'));c.setFont('Helvetica-Bold',27);c.drawString(50,465,title)
        c.setFillColor(HexColor('#e4ebf4'))
        lines=[line for bullet in bullets for line in textwrap.wrap(bullet,width=112)]
        size=min(16,max(6,350/max(len(lines),1)-3));c.setFont('Helvetica',size)
        for j,line in enumerate(lines):c.drawString(55,420-j*(size+3),line)
        if title=='Entrenamiento y curvas':
            curves=list(Path('resultados/curvas_entrenamiento').glob('**/loss.png'))
            for j,path in enumerate(curves[:2]):
                c.drawImage(str(path),45+j*445,65,width=425,height=205,preserveAspectRatio=True)

        c.setFont('Helvetica',11);c.drawString(50,30,'Evidencia y limitaciones: docs/estado_ejecucion.md');c.drawRightString(910,30,f'{i}/12');c.showPage()
    c.save()
    print('presentacion.pdf: 12 páginas; docs/estado_ejecucion.md actualizado')

if __name__=='__main__':main()
