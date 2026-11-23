# Auditoría científica de SP-06 para RPMESP

## Alcance y conservación

El punto de partida es 2dfc3941b7bf95ff690e899f9fba60eaeec08a1f. La rama research/rpmesp-audit-20261123 conserva los cambios locales previos en el commit 0aab220. Los archivos históricos y las corridas locales se conservan. PROTOCOLO.md describe tasas por 100 000 y redes neuronales. protocol_v2.py y research.py operan con probabilidad porcentual SH.DYN.NCOM.ZS. El protocolo editorial de este directorio es independiente del histórico.

## Hallazgos y correcciones

La selección excluía persistencia mediante drop. Ahora todos los métodos participan en la selección histórica con MAE log comparable y la interfaz informa por separado el mejor modelo ajustable. Persistencia se guarda, recupera e interpreta como referencia explícita.

La búsqueda histórica de ocho ensayos no superaba la fase inicial TPE predeterminada de diez ensayos. Los experimentos nuevos fijan presupuestos de 10, 30 y 60, n_startup_trials=10 y semilla 606. Diez ensayos constituyen un control de muestreo inicial. Se desactiva la poda para comparar los tres cortes temporales internos completos. Los ensayos se escriben inmediatamente en JSONL con estado, parámetros, duración y objetivo.

data_audit.json documenta que el hash publicado 26cc4eb59d77493b19d4a0e3d71a3024401c767cd46892f27bcc532d21ac0d70 corresponde a LF. El archivo Windows efectivamente analizado usa CRLF y su hash es a0556b00767935eb7f9b42a690126df9934531a0e16576a42ee3895f71fcbf6d. Se registra también una representación canónica del contenido. Los manifiestos nuevos registran commit, cambios locales y huellas del código. dependencies.lock.txt congela las versiones del entorno auditado.

## Protocolo congelado exploratorio

protocol.json define el diseño antes de los experimentos. Cada origen externo anual de 2013–2018 usa exclusivamente años anteriores para ajustar. La búsqueda interna usa los tres años inmediatamente anteriores al origen externo, con ventanas expansivas. Las variables de evaluación se construyen con observaciones previas disponibles. Se mantiene una historia común de cinco años para comparar ablaciones sobre las mismas celdas. Las escalas MASE usan diferencias anuales de la historia de cada país anterior al origen. La métrica primaria es MAE en puntos porcentuales. Se publican también RMSE, MASE, diferencia frente a persistencia, intervalos por bootstrap de países, errores por país-año y porcentaje de países con menor MAE.

Los resultados de 2019–2021 ya fueron examinados. Este protocolo trata las nuevas comparaciones como exploratorias. El mínimo observado entre múltiples modelos, presupuestos y variables exige evaluación adicional. La revisión API new_data_check.json no encontró valores posteriores a 2021 para Perú. La comprobación de otros países, versiones históricas y fechas de disponibilidad permanece necesaria antes de declarar una evaluación prospectiva.

## Variables y covariables

Se comparan tres rezagos, cinco rezagos y cinco rezagos con diferencia, cambio relativo, media, pendiente, volatilidad y distancia a la tendencia. Cada conjunto se evalúa para nivel logarítmico y diferencia anual directa. Las covariables externas requieren fuentes, unidad, cobertura y fechas de publicación. Ninguna covariable contemporánea sin metadatos de disponibilidad se incorpora automáticamente.

## Calibración

Se comparan cuantiles empíricos, rango conformal agrupado y máximos por bloque anual. Cada evaluación anual usa errores de años estrictamente anteriores. intervals.csv conserva cobertura y ancho por país y año. Con pocos bloques, el rango conformal puede exceder el tamaño muestral. La regla corregida devuelve toda la región válida 0–100 % y marca full_support_due_to_small_n. recalibrate.py aplica esta corrección de intervalos a las predicciones ya generadas. Los métodos pooled dependen de supuestos de intercambiabilidad que el panel temporal puede incumplir. La dependencia entre países y el cambio temporal impiden una garantía automática de cobertura. Los análisis 2020–2021 y la calibración condicional por país quedan como extensión retrospectiva independiente del ranking de desarrollo.

## Límites de la auditoría

La incertidumbre del bootstrap corresponde al remuestreo de países condicionado a las predicciones existentes. Los estudios temporales no sustituyen la transferencia geográfica del protocolo histórico. ARIMA(1,1,0), ETS amortiguado, media de tres años y deriva amortiguada a 0,5 son referencias preespecificadas con parámetros fijos. Los resultados no justifican causalidad ni uso clínico individual. CatBoost requiere su dependencia instalada.

La página editorial de RPMESP no estuvo disponible durante la consulta directa. Deben verificarse los límites de extensión, referencias y elementos gráficos en las instrucciones vigentes antes del envío. El manuscrito deberá distinguir el protocolo histórico, el análisis exploratorio nuevo y una eventual confirmación independiente.

La consulta de los 20 países, conservada en new_data_check_all.json, encontró 2021 como último año en todos ellos. La actualización general de WDI del 11 de noviembre de 2026 no implica nuevos años para este indicador.

El lote examined_baselines agrega un análisis retrospectivo de cobertura hasta 2021 únicamente para referencias fijas. Su configuración se guarda aparte y sus resultados no forman parte del ranking de desarrollo. Las advertencias de convergencia de ARIMA requieren revisar los ajustes individuales antes de atribuir utilidad al método.

El primer intento de ablación se interrumpió por sobrecarga de hilos OpenMP. Se conserva en ablations-interrupted y se repitió con OMP_NUM_THREADS=1, MKL_NUM_THREADS=1 y OPENBLAS_NUM_THREADS=1. El lote trees-interrupted conserva el intento de 30 ensayos de bosque aleatorio. Únicamente sus experimentos de diez ensayos con seis orígenes completos se recuperan en forest. Los parciales se excluyen del resumen. Para los demás árboles se limitó el lote a diez ensayos por búsqueda. El lote forest_both completa nivel y diferencias de bosque aleatorio con diez ensayos. Quedan pendientes 30 y 60 en estos algoritmos.

## Reproducción

Ejecutar python sp06_crisp/research.py --output CARPETA_NUEVA. Los argumentos --models, --budgets y --features permiten establecer explícitamente el lote. Los directorios de salida existentes se rechazan para conservar resultados previos. Cada directorio contiene predictions.csv, experiments.csv, intervals.csv, trials.jsonl para modelos ajustables y manifest.json.

Ejecutar python -m unittest discover -s sp06_crisp -p "test_*.py" para verificar límites, variables pasadas, unidades, duplicados y recuperación de persistencia.

## Organización de módulos de investigación

research_features.py construye exclusivamente variables históricas. research_models.py define referencias y espacios de búsqueda. research_calibration.py implementa el cuantil y su caso de muestra insuficiente. research.py coordina optimización temporal, predicciones y métricas. protocol_v2.py conserva la ingesta validada y la evaluación geográfica usada por la app. science/compile_results.py exporta comparaciones, errores, estabilidad y figuras. science/recalibrate.py conserva las predicciones y revisa únicamente las bandas con la regla de soporte completo.

El código ejecutado durante los lotes se archiva en executed_sources.zip y bounded_sources.zip. Los manifiestos indican la huella del archivo de ejecución anterior a esta extracción de funciones. La extracción mantiene los mismos cálculos. El manifiesto de intervalos registra por separado la corrección del rango conformal.

Para limitar hilos en Windows, configurar OMP_NUM_THREADS=1, MKL_NUM_THREADS=1 y OPENBLAS_NUM_THREADS=1 antes de iniciar Python. El número de ensayos es el presupuesto principal, sin timeout en los lotes de investigación.
