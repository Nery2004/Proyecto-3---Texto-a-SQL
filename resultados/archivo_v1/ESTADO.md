# Experimento preliminar invalidado

Primera ejecución real del modelo base con 48 propuestas de preguntas. Este snapshot se conserva para auditoría, pero no constituye el resultado final: se detectaron preguntas con codificación dañada y columnas de referencia que no estaban solicitadas explícitamente. Se corrige la generación por reglas generales para entrenamiento y validación; no se ajustan preguntas según aciertos del modelo.

Los tiempos, SQL y resultados aquí registrados fueron medidos realmente. Su EX no debe presentarse como estimación final de calidad. El JSONL preserva exactamente las entradas utilizadas. Los archivos del primer experimento se archivan al finalizar el proceso.

Para recuperar los fixtures de esta corrida consultar el commit `6a972ed` y
sus archivos `datos/esquemas/*/seed.sql`. Posteriormente se modificaron tanto
las preguntas como los fixtures: relaciones con varios hijos, padres sin hijos,
empates, agrupaciones repetidas y dos años de fechas. Por ello la diferencia
entre esta corrida y el baseline definitivo **no es una mejora del modelo**.
El modelo base y el prompt no se modificaron para explicar esa diferencia.
