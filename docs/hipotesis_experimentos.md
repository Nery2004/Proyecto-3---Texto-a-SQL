# Hipótesis previas al entrenamiento

Fecha de preparación: 25 de octubre de 2026. Autor: Codex (asistencia de IA).
Estado: hipótesis prospectivas; no se ha entrenado ningún adapter al escribir este documento.

H1: QLoRA A, rank 8, puede mejorar EX ponderada frente al modelo base al especializar formato SQL MySQL y preguntas en español. Puede perjudicar esquemas no vistos si memoriza patrones sintéticos.

H2: QLoRA B, rank 16, puede aumentar capacidad de adaptación respecto a A, con mayor memoria y tiempo. No se presupone que mejore EX; el aumento de capacidad puede agravar sobreajuste.

Única variable experimental: rank (8/16). Se mantienen alpha=16, dropout=0.05, seed=2026, modelo y revisión, datos y orden, 3 épocas, LR 0.0002, batch efectivo 16, AdamW, cosine, warmup 0.03, longitud 2048, módulos y NF4 double quantization FP16. Las rutas de salida identifican ejecuciones y no son factores del modelo. Alpha/r cambia como consecuencia matemática de mantener alpha fijo.

La pérdida se calcula únicamente sobre respuesta SQL; los tokens de esquema/pregunta se enmascaran con -100. Se rechazan ejemplos demasiado largos en lugar de truncar SQL o tablas. No hay validation loss: los esquemas independientes se reservan para EX posterior y no se usan para ajuste ni selección de checkpoints. Se usa el checkpoint final de cada ejecución.

Comparación: ejecutar baseline antes de entrenar; ejecutar A y B en procesos separados sobre la misma T4 y el mismo archivo de datos, verificar SHA256 registrado. Usar prompt compartido con inferencia, generación greedy y mismo protocolo de evaluación. Evaluar EX ponderada, categorías de error, latencias, VRAM y pérdida. Elegir adapter por EX observada respetando tiempo; documentar empate por latencia/memoria. La validación propia debe ser revisada por estudiantes antes de atribuir autoría humana.

Los experimentos no tienen resultados todavía. Las curvas se producen solamente a partir de trainer.state.log_history. Un fallo guarda run.json con estado fallido; no crea un adapter final ficticio. Los adapters no se copian automáticamente a adapter/: elegir después de evaluación real.
