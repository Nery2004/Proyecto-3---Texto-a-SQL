"""Promueve solo adapters completos evaluados; nunca crea pesos sustitutos."""
import csv
import hashlib
import json
from pathlib import Path
import shutil

def main():
    path=Path('resultados/resumen_comparacion.csv')
    rows=list(csv.DictReader(path.open(encoding='utf-8')))
    candidates=[]
    for name in 'ab':
        folder=Path(f'adapters_experimentos/config_{name}')
        run=json.loads((folder/'run.json').read_text(encoding='utf-8'))
        if run['estado']!='completado':raise RuntimeError(f'Experimento {name} incompleto')
        matches=[r for r in rows if r['modelo']==f'inference_{name}']
        if {r['estrategia'] for r in matches}!={'directa','callback'}:
            raise RuntimeError('Cada adapter debe evaluarse en ambas estrategias')
        callback=next(r for r in matches if r['estrategia']=='callback')
        direct=next(r for r in matches if r['estrategia']=='directa')
        candidates.append({'experimento':name,'ex_callback':float(callback['ex_ponderada']),
                           'ex_directa':float(direct['ex_ponderada']),
                           'latencia_callback':float(callback['latencia_promedio'])})
    best=max(candidates,key=lambda x:(x['ex_callback'],x['ex_directa'],-x['latencia_callback']))
    source=Path(f"adapters_experimentos/config_{best['experimento']}")
    target=Path('adapter');target.mkdir(exist_ok=True)
    for name in ['adapter_config.json','adapter_model.safetensors','run.json']:
        if not (source/name).is_file():raise FileNotFoundError(source/name)
        shutil.copy2(source/name,target/name)
    report={'seleccion':best,'candidatos':candidates,
            'criterio':'Mayor EX callback; desempate EX directa, luego menor latencia callback. Selección sobre validación propia; puede sobreajustar.',
            'sha256_pesos':hashlib.sha256((target/'adapter_model.safetensors').read_bytes()).hexdigest()}
    Path('resultados/seleccion_adapter.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
