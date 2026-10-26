"""Genera presentación y estado usando únicamente evidencia existente."""
import csv
import json
from pathlib import Path
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

def read_json(path, default=None):
    p=Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def main():
    stats=read_json('datos/fuentes/estadisticas.json',{})
    train=stats.get('entrenamiento',{});valid=stats.get('validacion',{})
    load=read_json('resultados/metricas/carga_baseline.json',{'estado':'pendiente'})
    unit=read_json('resultados/metricas/pruebas.json',{})
    integration=read_json('resultados/metricas/mysql_integration.json',{})
    runs={name:read_json(f'adapters_experimentos/config_{name}/run.json',{'estado':'no ejecutado'}) for name in 'ab'}
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
    phase=[('Inicialización y Git','Implementado; privacidad verificada, acceso docente pendiente'),
           ('Dataset',f"{train.get('aceptados',0)} aceptados MySQL; revisión semántica pendiente"),
           ('Validación',f"{valid.get('aceptados',0)} propuestas ejecutadas; autoría humana pendiente"),
           ('Baseline',ex),('QLoRA A',runs['a']['estado']),('QLoRA B',runs['b']['estado']),
           ('Inferencia','Contrato y pruebas unitarias implementados; T4 y latencia pendientes'),
           ('Experimento y errores','Pipeline implementado; resultados dependen de ejecución real'),
           ('Pruebas',f"Unitarias: {unit}; integración MySQL: {integration.get('aprobadas',0)} aprobadas"),
           ('Colaboración','Actividad IA declarada; contribuciones de ambos integrantes no acreditadas')]
    text='# Estado real de ejecución\n\n**Estado general: PARCIAL.** No es una entrega final entrenada.\n\n'
    text+='| Fase | Evidencia/estado |\n|---|---|\n'+''.join(f'| {a} | {b} |\n' for a,b in phase)
    text+='\n## Carga real del modelo\n\n```json\n'+json.dumps(load,ensure_ascii=False,indent=2)+'\n```\n'
    text+='\n## Pendientes obligatorios\n\nRevisar semántica y autoría estudiantil; completar baseline y dos entrenamientos comparables; evaluar adapters, seleccionar y entregar pesos reales; medir T4, tiempos y determinismo; ejecutar experimento directa/callback; analizar errores y justificar predicción EX; compartir con docente; aportes reales de ambos integrantes y entrega Canvas.\n'
    Path('docs/estado_ejecucion.md').write_text(text,encoding='utf-8')
    slides=[
      ('Proyecto 3: Texto a SQL',['Universidad del Valle de Guatemala | Deep Learning 2026','Profesor: Kevin Recinos','25 de octubre de 2026','Estado PARCIAL: ver evidencia, sin métricas inventadas']),
      ('Objetivo y contrato',['DDL MySQL con comentarios + pregunta en español','solucion.generar_sql(esquema, pregunta, ejecutar=None) -> str','Una consulta SELECT o WITH ... SELECT','Carga <=300s; pregunta <=30s; callback <=3 llamadas']),
      ('Arquitectura',['Prompt compartido -> Qwen local -> limpieza -> validación AST','Modelo diferido/cacheado; NF4 GPU; generación greedy','Callback opcional: ejecutar y corregir errores','Usuario SELECT-only y transacción READ ONLY']),
      ('Modelo y datos',['Qwen/Qwen2.5-Coder-1.5B-Instruct',f"{train.get('aceptados',0)} pares aceptados: ejecución MySQL 8.4.10",'Diez esquemas propios; deduplicación normalizando literales',f"Descartados: {train.get('descartados',0)}; revisión semántica pendiente"]),
      ('Validación independiente',['Hotelería y manufactura: dominios ausentes en entrenamiento',f"{valid.get('aceptados',0)} propuestas ejecutadas; 48 fijadas para comparación",'Fácil/media/difícil; partición por esquema','Propuestas IA: revisión/redacción humana pendiente']),
      ('Baseline',[f'Carga real: {load.get("estado")}',f'EX: {ex}','Mismo prompt, modelo base y semilla con/sin adapter','No hay cifras de rendimiento si no existen CSV medidos']),
      ('Hipótesis previas',['H1: rank8 puede especializar formato MySQL/español','H2: rank16 aporta capacidad y riesgo de sobreajuste','No se presupone mejora; EX oculto desconocido','Hipótesis guardadas antes de entrenar']),
      ('Dos configuraciones QLoRA',['Único factor: rank 8 frente a 16','Alpha16; dropout0.05; LR2e-4; 3 épocas; batch efectivo16','NF4 doble cuantización FP16; gradient checkpointing','Loss solo respuesta SQL; no se entrena con validación']),
      ('Entrenamiento y curvas',[f"A: {runs['a']['estado']}",f"B: {runs['b']['estado']}",'run.json registra tiempos, parámetros, pasos y VRAM','No se muestran curvas sin pasos de entrenamiento reales']),
      ('Experimento de inferencia',['Directa frente a ejecución/corrección sobre iguales ejemplos','EX ponderada con pesos1/2/3 y penalización de tiempos','Comparación de resultados: duplicados, orden, redondeo','Resultados pendientes si no existen registros reales']),
      ('Pruebas y errores',[f'Pruebas unitarias: {unit}',f"Integración MySQL: {integration.get('aprobadas',0)} PASS",'Categorías: sintaxis, tabla, columna, JOIN, agregado, filtro, resultado','Predicción EX: pendiente; EX oculto no conocido']),
      ('Entrega y pendientes',['Repositorio privado y pushes main verificables','Faltan pesos finales y experimentos si no se completaron','Faltan acceso docente y colaboración humana verificable','Uso de Codex y propuestas de datos IA declarado'])]
    c=canvas.Canvas('presentacion.pdf',pagesize=(960,540))
    for i,(title,bullets) in enumerate(slides,1):
        c.setFillColor(HexColor('#101b30'));c.rect(0,0,960,540,fill=1,stroke=0)
        c.setFillColor(HexColor('#69d6c5'));c.setFont('Helvetica-Bold',27);c.drawString(50,465,title)
        c.setFillColor(HexColor('#e4ebf4'));c.setFont('Helvetica',17)
        for j,line in enumerate(bullets):
            c.drawString(55,385-j*58,line[:102])
        c.setFont('Helvetica',11);c.drawString(50,30,'Evidencia y limitaciones: docs/estado_ejecucion.md');c.drawRightString(910,30,f'{i}/12');c.showPage()
    c.save()
    print('presentacion.pdf: 12 páginas; docs/estado_ejecucion.md actualizado')

if __name__=='__main__':main()
