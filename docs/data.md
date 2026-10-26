# Datos propios y ejecución MySQL

Los dominios se definen en `src/data/generate.py`. Se generan 10 esquemas de entrenamiento (universidad, hospital, banco, tienda, inventarios, restaurante, biblioteca, transporte, rrhh y reservaciones) y 2 completamente separados (hotelería y manufactura). Los grafos tienen 3–5 tablas y relaciones distintas, con 12 filas deterministas por tabla. Las cifras exactas se registran en `datos/fuentes/estadisticas.json`.

Las preguntas y consultas son propuestas originales de Codex a partir de plantillas semánticas, sin datasets externos. No se atribuyen a estudiantes. La variación incluye proyecciones, filtros, agregaciones, relaciones, anti-joins, HAVING, fechas, CTE, ventanas y subconsultas. Los umbrales también varían; esta generación controlada no reemplaza una revisión humana ni garantiza generalización.

1. Define `MYSQL_ROOT_PASSWORD` y `MYSQL_READONLY_PASSWORD` mediante variables locales o un archivo `.env` excluido de Git. Docker Compose lee `.env`, Python usa variables del proceso.
2. Ejecuta `docker compose up -d` y espera a que MySQL esté saludable.
3. Ejecuta `python scripts/build_dataset.py generate` para reconstruir propuestas y fixtures. **Esto reinicia los archivos aceptados; no ejecutar después de validar salvo reconstrucción deliberada.**
4. Ejecuta `python scripts/build_dataset.py initialize` una vez en bases vacías. Crea las bases, tablas, fixtures y un usuario con exclusivamente SELECT por base. No sobrescribe tablas existentes. El administrador solo prepara fixtures; nunca ejecuta consultas candidatas.
5. Ejecuta `python scripts/build_dataset.py validate`. Exige versión exacta 8.4.10, ONLY_FULL_GROUP_BY y privilegios exclusivamente SELECT; aplica AST, transacción READ ONLY y máximo 5 segundos por SELECT. Guarda evidencia de ejecución en `aceptados.jsonl`, descartes y estadísticas.
6. Revisa semánticamente las preguntas y redacta/edita la validación con autoría humana real. `revision_humana` y `revision_semantica` permanecen pendientes hasta dicha revisión. Una consulta ejecutable no demuestra equivalencia semántica.

Los registros JSONL contienen id, schema_id, DDL, pregunta, SQL, dificultad, tipo, origen, estado de validación, exigencia de orden y estado de revisión humana. Solo los archivos `aceptados.jsonl` pasan al entrenamiento. Cada aceptado identifica versión y fecha UTC de ejecución. La separación se hace por dominio completo, sin compartir schema_id entre conjuntos. Las consultas con errores se conservan en `datos/descartes/descartes.jsonl` con clasificación y mensaje real.

Para evaluación, `src.data.mysql.MySQLExecutor(schema_id)` funciona como callback y devuelve `ok`, `columnas`, `filas` y `error`; permite `with` y `.close()`. Usa las mismas variables y conserva la conexión. Las limitaciones son fixtures pequeños, propuestas sintéticas, ausencia de autoría estudiantil confirmada y revisión semántica pendiente.

Ejecuci?n realizada: MySQL 8.4.10 en Docker, con todas las consultas aceptadas ejecutadas realmente. `datos/fuentes/mysql_evidence.json` conserva versi?n, sql_mode, privilegios SELECT y hashes SHA-256 del snapshot validado. La plantilla `datos/validacion/revision_humana.csv` deja en blanco autor, fecha y redacci?n humana.
