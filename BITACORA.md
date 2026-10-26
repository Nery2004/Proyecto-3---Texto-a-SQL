# Bitácora real de esta ejecución

Todas las entradas corresponden al 25 de octubre de 2026 (America/Los_Angeles).
Autor de las ocho entradas: **Codex, asistencia de IA**. No se afirma actividad
académica previa ni participación humana sin evidencia.

1. Inspección del repositorio: rama main sin commits, remoto verificado y GPU RTX 4060 8GB detectada. Evidencia: ROADMAP.md y primer commit a31a076.
2. Lectura completa del PDF oficial de 3 páginas encontrado en Descargas. Se adoptó el contrato y MySQL 8.4.10. Evidencia: README.md, solucion.py.
3. Implementación de inferencia diferida, prompt común y validación AST. Veinte pruebas iniciales aprobadas. Evidencia: a31a076, tests/test_inference.py.
4. Cambio efectivo del repositorio de público a privado con credenciales del gestor Git; sin exponer valores. Evidencia: 7482a7f, docs/github_access.json.
5. Implementación de EX por ejecución y reglas de comparación, con clasificación de errores y límites. Evidencia: 6b4897e, src/evaluation/.
6. Arranque del motor Docker y de MySQL 8.4.10; ejecución inicial de 2262 pares de entrenamiento y 463 propuestas independientes, sin descartes. Evidencia: 66950ff y JSONL con fechas de ejecución.
7. Preparación de hipótesis previas, dos configuraciones QLoRA con rank como único factor y tres notebooks Colab. Evidencia: fd9cf77, docs/hipotesis_experimentos.md.
8. Instalación aislada de PyTorch CUDA y auditoría de configuraciones, caché, modo base/adapter y seguridad. Evidencia: requirements.txt, tests/test_config.py; los experimentos reales se registran separadamente en resultados/metricas/.

El historial `historial_git.txt` es un snapshot generado con
`git log --all --date=iso --stat`. Por construcción no incluye su propio commit
posterior. Regenerar con el mismo comando al preparar la entrega final.
