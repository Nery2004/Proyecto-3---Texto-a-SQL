# Evaluación por ejecución

`src/evaluation` compara resultados reales devueltos por el callback MySQL.
EX suma pesos de aciertos y divide entre los pesos de todas las preguntas:
fácil 1, media 2 y difícil 3. Una referencia no ejecutable aborta el ensayo,
en lugar de producir una métrica engañosa. Un conjunto vacío no tiene EX.

El comparador redondea números a dos decimales con Decimal y ROUND_HALF_UP.
Conserva NULL, tipos de texto y multiplicidad de filas. El orden se compara
solamente si el ejemplo indica `orden_importa: true`. Ignora los alias de
columnas y permite eliminar exactamente una columna adicional del resultado
candidato, en cualquier posición. No permuta las columnas restantes. Resultados
vacíos exigen también cantidades de columnas compatibles. Esta política y el
redondeo son convenciones explícitas; deben contrastarse con el evaluador oficial.

Ejecutar, con MySQL inicializado y modelos disponibles:

```powershell
python scripts/evaluate.py --dataset datos/validacion/validacion.jsonl --config config_baseline.json --config config_lora_a.json --config config_lora_b.json
```

Cada configuración debe mantener modelo base, semilla y parámetros de inferencia;
solo cambia el adapter y su activación. `TEXT2SQL_CONFIG` selecciona cada archivo.
El mismo conjunto y el mismo generador evalúan estrategias directa y callback.
`--executor-factory modulo:funcion` admite una fábrica propia que recibe schema_id
y devuelve un callback de solo lectura con ok, columnas, filas y error.

Se precarga el runtime y mide el límite de carga de 300 segundos. La latencia por
pregunta incluye generación y callbacks internos; la ejecución final de puntuación
y referencia quedan fuera de ese presupuesto. Más de 30 segundos o más de tres
intentos de llamada al callback impiden contabilizar éxito. No se cancelan kernels
GPU por fuerza: las infracciones se registran tras retornar. El generador debe
aplicar su propio presupuesto de generación.

Los CSV conservan SQL, resultado observado, errores, latencias, llamadas y límites.
Los resúmenes incluyen EX y reparaciones exitosas/fallidas: una reparación requiere
al menos un error observado en callback. Una consulta semánticamente incorrecta
que simplemente se ejecuta no se cuenta automáticamente como reparada. Los errores
MySQL conocidos reciben categoría reproducible. Tras confirmar un resultado
distinto por ejecución, se comparan firmas AST MySQL normalizadas de JOIN,
agregaciones/GROUP BY/HAVING y WHERE. Si cambia exactamente una familia, se propone
esa categoría como hipótesis; si cambian varias o ninguna, se conserva
`resultado_diferente`. Toda hipótesis semántica lleva `revision_humana=true`:
estructuras distintas pueden ser equivalentes y la diferencia AST nunca determina
exactitud. Los CSV por dificultad y modelo muestran EX, errores y latencias.

Los callbacks enviados al generador incluyen como máximo diez filas, igual que el
contrato oficial. Las referencias y candidatos finales se puntúan con el resultado
completo del ejecutor. El ejecutor local aborta resultados mayores de 10,000 filas;
una referencia que supera ese límite bloquea el experimento en vez de puntuar una
muestra parcial.

El script produce comparaciones CSV y PNG exclusivamente al ejecutar evaluaciones.
Las pruebas unitarias usan callbacks controlados y no demuestran calidad del modelo,
ni acceso a MySQL, ni rendimiento real en T4. EX oculto permanece desconocido;
una predicción requiere resultados independientes reales y análisis de generalización.
