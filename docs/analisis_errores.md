# Análisis de resultados medidos

La EX se obtiene de ejecución. Las categorías estructurales son hipótesis para revisión humana, nunca evidencia automática de causa semántica.

| Modelo/estrategia | EX | EX por dominio |
|---|---:|---|
| baseline/callback | 0.6250 | {'hoteleria': 0.5208333333333334, 'manufactura': 0.7291666666666666} |
| baseline/directa | 0.6250 | {'hoteleria': 0.5208333333333334, 'manufactura': 0.7291666666666666} |

## Efecto de LoRA


## Experimento de inferencia

- baseline: directa EX 0.6250, 1.43s; callback EX 0.6250, 3.40s. Recomendación operativa: directa, por mayor EX y desempate en latencia.

La modalidad directa se invoca con ejecutar=None. Se conserva la capacidad de reparación cuando el evaluador aporta callback; ambas modalidades se midieron bajo el mismo prompt y límites. La recomendación no garantiza que la corrección ayude en otros dominios.

## Revisión y mejoras

Consultar errores.csv para pregunta, esquema, referencia, SQL producido, resultado y error. Revisar manualmente todas las categorías antes de atribuir causas. Priorizar nombres inventados, agregaciones y cardinalidad JOIN según frecuencias reales del JSON. Más dominios y redacción humana independiente reducirían el sesgo de plantillas. La ejecución sobre un fixture no garantiza equivalencia en todos los datos posibles.
