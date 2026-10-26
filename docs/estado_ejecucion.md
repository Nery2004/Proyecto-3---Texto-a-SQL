# Estado real de ejecución

**Estado general: PARCIAL.** Persisten requisitos humanos y verificación Colab T4.

| Fase | Evidencia/estado |
|---|---|
| Inicialización y Git | Implementado; privacidad verificada, acceso docente pendiente |
| Dataset | 2440 aceptados MySQL; revisión semántica pendiente |
| Validación | 478 propuestas ejecutadas; autoría humana pendiente |
| Resultados medidos | baseline/directa: EX 0.6250; n=48; media 1.43s; máx 4.45s; fuera límite 0<br>baseline/callback: EX 0.6250; n=48; media 3.40s; máx 25.84s; fuera límite 0 |
| QLoRA A | LoRA A: en_curso; pasos no registrados; tiempo no registrados |
| QLoRA B | LoRA B: no ejecutado; pasos no registrados; tiempo no registrados |
| Selección | Adapter final pendiente de selección medida |
| Inferencia | GPU medida: NVIDIA GeForce RTX 4060 Laptop GPU; T4 no verificada |
| Experimento y errores | Pipeline implementado; resultados dependen de ejecución real |
| Pruebas | Unitarias: {'aprobadas': 53, 'fallidas': 0, 'omitidas': 0}; integración MySQL: 8 aprobadas |
| Colaboración | Trabajo individual confirmado por el estudiante; asistencia de Codex declarada |

## Carga real del modelo

```json
{
  "config": "configs/baseline.json",
  "estado": "completado",
  "carga_modelo_segundos": 95.34399999999732,
  "segundos_totales": 115.80309539999871
}
```

## Pendientes obligatorios

Revisar semántica y redacción/autoría estudiantil de las propuestas IA; verificar ejecución y rendimiento Colab T4; acceso docente pendiente (el estudiante desconoce su usuario GitHub); entrega Canvas. Entrenamientos, evaluaciones y selección siguen pendientes si falta su evidencia medida arriba. Trabajo individual declarado: no se atribuyen aportes a otro integrante.

## Predicción y límites

Predicción pendiente de selección y análisis medidos; EX oculta desconocida.

Dos dominios sintéticos y selección sobre la misma validación pueden sobreestimar generalización. El mínimo por dominio no es límite inferior ni intervalo de confianza.
