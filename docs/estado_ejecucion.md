# Estado real de ejecución

**Estado general: PARCIAL.** No es una entrega final entrenada.

| Fase | Evidencia/estado |
|---|---|
| Inicialización y Git | Implementado; privacidad verificada, acceso docente pendiente |
| Dataset | 2440 aceptados MySQL; revisión semántica pendiente |
| Validación | 478 propuestas ejecutadas; autoría humana pendiente |
| Baseline | Pendiente: no se ha medido EX |
| QLoRA A | no ejecutado |
| QLoRA B | no ejecutado |
| Inferencia | Contrato y pruebas unitarias implementados; T4 y latencia pendientes |
| Experimento y errores | Pipeline implementado; resultados dependen de ejecución real |
| Pruebas | Unitarias: {'aprobadas': 49, 'fallidas': 0, 'omitidas': 0}; integración MySQL: 8 aprobadas |
| Colaboración | Actividad IA declarada; contribuciones de ambos integrantes no acreditadas |

## Carga real del modelo

```json
{
  "config": "configs/baseline.json",
  "estado": "iniciado"
}
```

## Pendientes obligatorios

Revisar semántica y autoría estudiantil; completar baseline y dos entrenamientos comparables; evaluar adapters, seleccionar y entregar pesos reales; medir T4, tiempos y determinismo; ejecutar experimento directa/callback; analizar errores y justificar predicción EX; compartir con docente; aportes reales de ambos integrantes y entrega Canvas.
