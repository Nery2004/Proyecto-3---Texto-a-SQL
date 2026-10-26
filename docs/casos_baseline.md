# Casos del baseline revisados por Codex

Revisión técnica de IA sobre los CSV reales del baseline final previo al
entrenamiento. No es revisión humana ni prueba de equivalencia universal.
Se usa el conjunto corregido de 48 preguntas y los fixtures con cardinalidades
múltiples. La EX permanece calculada únicamente por resultados ejecutados.

| ID | Diferencia observada | Causa probable |
|---|---|---|
| hoteleria-00202 | Se pide agrupar noches por fecha; el modelo agrupa por huesped_id y agrega un JOIN | Agrupación y JOIN incorrectos; clasificación automática ambigua |
| hoteleria-00174 | Se pide rango denso global con empates; el modelo concatena mínimo y máximo y multiplica filas mediante JOIN | Confusión entre rango ordinal y intervalo; varias operaciones incorrectas |
| hoteleria-00094 | Se pide SUM(tarifa) por hotel_id; el modelo calcula una suma global y la repite para habitaciones | Pérdida de la agrupación y proyección solicitada |
| hoteleria-00175 | La referencia acumula desde el inicio hasta la fila actual; el modelo suma desde la fila actual hasta el final | Marco de ventana incorrecto |
| hoteleria-00209 | La desviación poblacional se convierte en una expresión con AVG anidado dentro de SUM | MySQL devuelve 1111: uso inválido de función de grupo |
| hoteleria-00159 | El modelo ordena el segundo criterio id de forma descendente | Orden incorrecto en empates, detectado por fixtures con valores repetidos |
| manufactura-00031 | El modelo ordena costo en sentido descendente | Orden contrario al ASC por defecto adoptado en las referencias |

Las categorías AST sugieren causas y requieren revisión. El código incorpora
el error MySQL 1111 en agregación e inspecciona marcos de ventana; no convierte
diferencias de AST en aciertos o fallos de EX. Las preguntas que dicen
«ordenados por X y después Y» usan ASC por omisión en sus referencias. La
revisión humana pendiente debería explicitar ese sentido al redactar la versión
estudiantil, manteniendo el protocolo idéntico entre modelos si se reevalúa.

Hipótesis verificable para la comparación posterior: LoRA puede mejorar la
vinculación entre las instrucciones españolas, identificadores del DDL y
estructuras GROUP BY/ventanas. Las mejoras y regresiones deben verificarse en
los CSV de A y B; estos casos del baseline no permiten anticipar sus resultados.
