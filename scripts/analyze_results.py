"""Análisis auditable por categoría y dominio; estimación oculta explícita como heurística."""
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path
from src.evaluation.metrics import weighted_ex

def main():
    rows=list(csv.DictReader(Path('resultados/comparacion_lora.csv').open(encoding='utf-8')))
    if not rows:raise RuntimeError('No hay experimentos medidos para analizar')
    for row in rows:row['resultado_correcto']=row['resultado_correcto']=='True'
    groups=defaultdict(list)
    for row in rows:groups[(row['modelo'],row['estrategia'])].append(row)
    report={}
    for (model,strategy),records in sorted(groups.items()):
        by_schema={}
        for schema in sorted({r['schema_id'] for r in records}):
            by_schema[schema]=weighted_ex([r for r in records if r['schema_id']==schema])
        report[model+'/'+strategy]={'ex':weighted_ex(records),'ex_por_esquema':by_schema,
             'errores_por_categoria':dict(Counter(r['categoria_error'] for r in records if not r['resultado_correcto'])),
             'errores_por_dificultad':dict(Counter(r['dificultad'] for r in records if not r['resultado_correcto']))}
    Path('resultados/metricas/analisis_errores.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    text='# Análisis de resultados medidos\n\nLa EX se obtiene de ejecución. Las categorías estructurales son hipótesis para revisión humana, nunca evidencia automática de causa semántica.\n\n'
    text+='| Modelo/estrategia | EX | EX por dominio |\n|---|---:|---|\n'
    for key,value in report.items():text+=f"| {key} | {value['ex']:.4f} | {value['ex_por_esquema']} |\n"
    baseline=report.get('baseline/directa')
    if baseline:
        text+='\n## Efecto de LoRA\n\n'
        for key,value in report.items():
            if not key.startswith('baseline/') and key.endswith('/directa'):
                text+=f"- {key}: diferencia EX {value['ex']-baseline['ex']:+.4f} frente a baseline/directa.\n"
    inference={}
    text+='\n## Experimento de inferencia\n\n'
    for model in sorted({key[0] for key in groups}):
        if (model,'directa') not in groups or (model,'callback') not in groups:continue
        direct=groups[(model,'directa')];callback=groups[(model,'callback')]
        direct_ex=weighted_ex(direct);callback_ex=weighted_ex(callback)
        direct_time=sum(float(r['latencia_segundos']) for r in direct)/len(direct)
        callback_time=sum(float(r['latencia_segundos']) for r in callback)/len(callback)
        chosen_strategy='callback' if (callback_ex,-callback_time)>(direct_ex,-direct_time) else 'directa'
        inference[model]={'ex_directa':direct_ex,'ex_callback':callback_ex,
                          'media_directa_segundos':direct_time,'media_callback_segundos':callback_time,
                          'estrategia_recomendada':chosen_strategy,
                          'criterio':'Mayor EX; con empate, menor latencia observada. Las diferencias pequeñas de tiempo pueden ser ruido.'}
        text+=f"- {model}: directa EX {direct_ex:.4f}, {direct_time:.2f}s; callback EX {callback_ex:.4f}, {callback_time:.2f}s. Recomendación operativa: {chosen_strategy}, por mayor EX y desempate en latencia.\n"
    Path('resultados/metricas/experimento_inferencia.json').write_text(json.dumps(inference,indent=2),encoding='utf-8')
    text+='\nLa modalidad directa se invoca con ejecutar=None. Se conserva la capacidad de reparación cuando el evaluador aporta callback; ambas modalidades se midieron bajo el mismo prompt y límites. La recomendación no garantiza que la corrección ayude en otros dominios.\n'
    selected=Path('resultados/seleccion_adapter.json')
    if selected.exists():
        best=json.loads(selected.read_text())['seleccion'];key=f"inference_{best['experimento']}/callback"
        observed=report[key]['ex'];domains=list(report[key]['ex_por_esquema'].values())
        prediction=min(domains)
        text+=('\n## Predicción de EX oculta\n\n'
               f'EX observada seleccionada: {observed:.4f}. Predicción puntual heurística: {prediction:.2f} '
               '(mínima EX entre los dos dominios independientes observados; se toma el dominio de peor rendimiento como referencia conservadora). '
               f'Variación empírica entre dominios: {min(domains):.2f}–{max(domains):.2f}; no es un intervalo de confianza para el docente. '
               'La evidencia procede de dos dominios sintéticos, familias de preguntas compartidas y selección de adapter en la misma validación. '
               'Estos factores pueden sobreestimar generalización y las bases ocultas tienen más tablas; la predicción es frágil y no supone un límite inferior. '
               'La EX oculta del docente es desconocida.\n')
    text+='\n## Revisión y mejoras\n\nConsultar errores.csv para pregunta, esquema, referencia, SQL producido, resultado y error. Revisar manualmente todas las categorías antes de atribuir causas. Priorizar nombres inventados, agregaciones y cardinalidad JOIN según frecuencias reales del JSON. Más dominios y redacción humana independiente reducirían el sesgo de plantillas. La ejecución sobre un fixture no garantiza equivalencia en todos los datos posibles.\n'
    Path('docs/analisis_errores.md').write_text(text,encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
