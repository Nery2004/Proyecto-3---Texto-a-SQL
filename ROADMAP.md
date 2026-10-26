# Roadmap de ejecución

Estado inicial: repositorio sin commits. Especificación oficial leída íntegramente desde Proyecto_3_Texto_a_SQL.pdf (3 páginas).

- [x] Inicialización, dependencias y diagnóstico real.
- [x] Diez esquemas propios y >=2000 pares ejecutados en MySQL 8.4.10.
- [ ] Dos esquemas independientes y >=40 propuestas; revisión humana pendiente.
- [x] Inferencia greedy, validación AST y contrato; falta validar determinismo/T4 reales.
- [ ] Baseline real antes del entrenamiento.
- [ ] Dos QLoRA que difieren únicamente en rank, hipótesis previa.
- [ ] Evaluación por ejecución y experimento de reparación.
- [x] Pruebas CPU/MySQL, documentación y presentación; actualizar al finalizar experimentos.
- [ ] Commits/push a main y auditoría de entrega.

No se consideran completados entrenamientos ni validaciones sin evidencia.

Auditorías de datos: deduplicación de literales; reparación UTF-8; columnas
explícitas en preguntas; orden exterior por AST; fixtures con relaciones 1:N.
La primera corrida del baseline se conserva en resultados/archivo_v1 y está
invalidada para comparación final por ambigüedades del dataset anterior.
