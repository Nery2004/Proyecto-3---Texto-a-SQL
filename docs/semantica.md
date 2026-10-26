# Auditoría semántica automática independiente

`scripts/audit_semantics.py` interpreta un subconjunto explícito de preguntas en español mediante expresiones regulares. De la pregunta obtiene tabla, agrupación, métrica, agregado y condición. No lee el SQL de referencia para construir la respuesta esperada.

El auditor obtiene las filas mediante `SELECT *` usando `MySQLExecutor` con permisos exclusivamente SELECT y transacciones READ ONLY. Calcula en Python promedios, sumas, máximos, mínimos, conteos distintos, diferencias máximo–mínimo, desviación estándar poblacional y rangos densos con empates. También interpreta HAVING que compara el agregado de cada grupo con el promedio global de las filas. Conserva la semántica de NULL para los agregados soportados.

Después de calcular la respuesta esperada ejecuta el SQL de referencia y compara los resultados mediante `src.evaluation.metrics.compare_results`, con multiplicidad, redondeo a dos decimales y sin exigir orden exterior. Los controles negativos ejecutan deliberadamente SUM donde la pregunta pide AVG y comprueban que la discrepancia se detecta. Las preguntas fuera de la gramática se contabilizan como no aplicables, nunca como correctas.

Ejecuta, con las variables de acceso MySQL ya configuradas:

```bash
python scripts/audit_semantics.py
```

El único artefacto escrito es `resultados/metricas/semantic_oracle.json`, que registra conteos, cobertura, resultados por pregunta, controles negativos y hashes de los datasets. El script verifica que los JSONL permanezcan idénticos durante la ejecución. No modifica datos, esquemas, fixtures ni entradas de entrenamiento; puede usarse sobre el snapshot congelado de los experimentos A/B.

Esta auditoría fue creada por Codex y es automática. Su independencia consiste en calcular respuestas desde la pregunta y filas, sin derivarlas del SQL esperado; las preguntas siguen siendo propuestas sintéticas originadas en plantillas. No sustituye la revisión humana ni establece autoría estudiantil. La gramática y el comparador delimitan la cobertura: las familias no reconocidas y las diferencias inferiores al redondeo admitido requieren otros controles.
