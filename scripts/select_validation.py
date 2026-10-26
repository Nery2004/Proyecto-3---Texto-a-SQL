"""Subset fijo por esquema/dificultad para experimentar; conservar el mismo entre modelos."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

def main():
    source=Path('datos/validacion/aceptados.jsonl')
    buckets=defaultdict(list)
    for line in source.read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        buckets[(row['schema_id'],row['dificultad'])].append(row)
    chosen=[]
    for key,rows in sorted(buckets.items()):
        # hash fijo evita seleccionar solo primeros patrones del generador.
        chosen.extend(sorted(rows,key=lambda r:hashlib.sha256(r['id'].encode()).hexdigest())[:8])
    assert len(chosen)>=40 and len({r['schema_id'] for r in chosen})>=2
    target=Path('datos/validacion/evaluacion_48.jsonl')
    target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in chosen),encoding='utf-8')
    print(f'{len(chosen)} propuestas IA; revisión humana pendiente. SHA256: {hashlib.sha256(target.read_bytes()).hexdigest()}')

if __name__=='__main__': main()
