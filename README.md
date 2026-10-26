# Proyecto 3: Texto a SQL con QLoRA

Universidad del Valle de Guatemala, Deep Learning 2026. Especificación oficial:
`Proyecto_3_Texto_a_SQL.pdf`, leída íntegramente. **Entrega parcial en preparación**:
no confundir implementación con experimentos completados. Ver [estado real](docs/estado_ejecucion.md).

El sistema recibe DDL MySQL con comentarios y una pregunta en español. Un
Qwen/Qwen2.5-Coder-1.5B-Instruct local genera SQL con el chat template oficial;
SQLGlot valida el AST antes de ejecutar. El callback opcional permite hasta tres
intentos de consulta/corrección. No se usan APIs externas para inferencia.

## Instalación y diagnóstico

Python 3.10–3.12. Para GPU NVIDIA, instalar primero PyTorch CUDA compatible:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pip check
.venv\Scripts\python -m scripts.diagnose
.venv\Scripts\python -m pytest -q
```

En Linux/Colab usar `python` dentro del entorno y los mismos comandos pip. Los
tres notebooks permiten empezar desde un ZIP del repositorio privado. Elegir
GPU T4; sus celdas no ejecutadas no acreditan compatibilidad medida en T4.
Ver [dependencias](docs/dependencias.md) y [limitaciones](docs/limitaciones.md).

## Base de datos y datos

Crear `.env` local con `MYSQL_ROOT_PASSWORD`, `MYSQL_READONLY_PASSWORD` aleatorias
y `MYSQL_PORT` libre. Nunca subirlo a Git. `docker compose up -d` instala
**MySQL 8.4.10**, con valores por defecto incluyendo ONLY_FULL_GROUP_BY.

```powershell
python -m scripts.build_dataset generate
python -m scripts.with_env python -m scripts.build_dataset initialize
python -m scripts.with_env python -m scripts.build_dataset validate
python -m scripts.select_validation
```

`initialize` exige bases vacías y no sobrescribe tablas. `generate` reconstruye
archivos, por lo que solo debe ejecutarse al reconstruir deliberadamente el
dataset. Diez dominios son de entrenamiento; hotelería y manufactura quedan
reservados. Los JSONL aceptados tienen evidencia individual de versión y fecha
de ejecución. Las consultas candidatas solo se ejecutan con permisos SELECT.

Las preguntas son propuestas de IA basadas en plantillas originales. La revisión
semántica y las preguntas de validación escritas por estudiantes siguen pendientes.
No usamos Spider/BIRD ni atribuimos esas propuestas a personas. Ver
[datos y fuentes](docs/data.md), `datos/fuentes/estadisticas.json` y
`datos/validacion/revision_humana.csv`.

## Inferencia y entrenamiento

```python
from solucion import generar_sql
sql = generar_sql(esquema, "Lista los cinco clientes con más compras", ejecutar=None)
```

`config.json` conserva exactamente los cuatro campos exigidos. `usar_adapter=true`
requiere pesos entrenados reales en `adapter/`; si faltan, produce un error
explícito. Para el baseline usar `configs/baseline.json` mediante la variable
`TEXT2SQL_CONFIG`. El modelo se carga una vez, con NF4 en GPU, y se cachea.
Ambos modos comparten prompt, revisión de pesos base y generación greedy.

LoRA permite entrenar matrices pequeñas manteniendo congelado el modelo base;
QLoRA reduce memoria mediante cuantización 4-bit. A y B difieren solo en rank
8/16 (rutas identifican artefactos), con las
[hipótesis escritas antes del entrenamiento](docs/hipotesis_experimentos.md).
El loss se aplica solo a la respuesta SQL, sin incorporar esquemas de validación.

```powershell
python -m scripts.with_env python -m scripts.evaluate --dataset datos/validacion/evaluacion_48.jsonl --config configs/baseline.json --strategy ambas
python -m scripts.train --config configs/lora_a.json
python -m scripts.train --config configs/lora_b.json
```

Después evaluar ambos adapters con el mismo subset y protocolo; copiar el adapter
elegido completo a `adapter/` únicamente tras comparación real. Los checkpoints
no son entregables finales. No subir archivos mayores de 100 MB a Git normal:
usar Git LFS, comprobar descarga en Colab y entregar el ZIP con pesos físicos.

## Evaluación y entregables

La EX se calcula por resultados ejecutados, con pesos 1/2/3. Respeta duplicados,
redondea números a dos decimales, compara orden solo cuando se pide y admite una
columna adicional. No usa igualdad textual para decidir aciertos. El experimento
directa/callback comparte modelo y ejemplos. Se registran tiempos, reparaciones,
errores y violaciones del presupuesto. Ver [protocolo](docs/evaluacion.md).

`src/` contiene datos, entrenamiento, inferencia y evaluación; `scripts/` las
CLI; `datos/` esquemas/fixtures/JSONL; `notebooks/` las tres ejecuciones Colab;
`resultados/` evidencia y CSV; `tests/` las pruebas sin GPU; `presentacion.pdf`
resume solo evidencia real. El historial y la bitácora son trazables a commits.
Las métricas no medidas se indican como pendientes, nunca como cero observado.

## Licencias, IA y colaboración

Implementación y propuestas de datos creadas con asistencia de OpenAI Codex,
incluyendo agentes con funciones de datos, entrenamiento y evaluación. No se
presentan como trabajo independiente de dos integrantes. El usuario confirmó
que trabaja individualmente. Debe registrar únicamente sus aportes humanos
reales; no existe un segundo integrante al que atribuir contribuciones.

Qwen se usa bajo su licencia publicada en la
[ficha oficial](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct).
Las dependencias conservan sus licencias; los datos sintéticos no contienen datos
personales externos. No se asigna una licencia al código del estudiante sin su
decisión. El repositorio fue cambiado a privado con autorización del usuario;
falta verificar acceso del docente por no disponer de su usuario GitHub.
