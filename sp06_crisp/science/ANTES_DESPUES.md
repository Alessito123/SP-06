# Comparación técnica

| Aspecto | Flujo anterior | Rama de auditoría |
| --- | --- | --- |
| Selección | Persistencia excluida del ganador | Persistencia participa y el mejor ajustable se muestra aparte |
| Métrica histórica | MAE log de cinco folds geográficos | Se conserva para compatibilidad |
| Experimentos nuevos | Sin módulo independiente | MAE porcentual rolling-origin, seis años y tres cortes internos |
| TPE | Ocho ensayos por estudio | Presupuestos 10, 30 y 60 con diez iniciales explícitos |
| Poda | Mediana sobre pocos folds | Sin poda en los experimentos nuevos |
| Baselines | Persistencia | Deriva amortiguada, media móvil, ETS y ARIMA adicionales |
| Variables | Tres rezagos | Ablación de tres, cinco e ingeniería histórica |
| Objetivo | Nivel logarítmico | Nivel y diferencia anual directa |
| Incertidumbre | Cuantil pooled fijo de validación | Empírico, rango conformal y máximos por año con historia previa |
| Hash | Una huella sin contexto de codificación | Bytes reales, representación canónica y diagnóstico LF/CRLF |
| Código | Commit sin distinguir cambios locales | Commit, indicador dirty y huellas de los módulos |
| Resultados | Tablas de una corrida | Predicciones completas, ensayos JSONL y tablas por país y año |

Los ensayos de la rama son exploratorios. El hecho de ejecutar más configuraciones aumenta las oportunidades de encontrar mínimos por azar. El intervalo por países de un mínimo seleccionado no corrige ese efecto. Una conclusión confirmatoria requiere una evaluación externa preespecificada.

La interfaz conserva corridas antiguas con sus manifiestos. Las tablas anteriores a la corrección se interpretan según el algoritmo que las produjo y no se recalculan automáticamente.
