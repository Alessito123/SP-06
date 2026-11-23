# Cierre científico y reproducibilidad para RPMESP

## Dictamen

Se verificaron las predicciones de los 65 experimentos desde un clon limpio con Python 3.12.9 y dependencias científicas congeladas. Las 7 800 predicciones recalculadas coincidieron con las archivadas. La integración repite una búsqueda breve de Optuna en procesos independientes. Los 11 160 ensayos históricos completos no se reejecutaron.

El proyecto satisface un mínimo técnico de trazabilidad y reproducción de sus predicciones en el entorno Windows auditado. La evidencia predictiva conserva alcance exploratorio. La evaluación temporal adicional tampoco produjo evidencia clara de superioridad frente a persistencia. La aprobación editorial, las declaraciones de autores y la revisión institucional requieren confirmación humana.

## Ensayos de 30 y 60

Los presupuestos 10/30/60 se completaron para Ridge, Elastic Net e HistGradientBoosting. Random Forest, XGBoost y CatBoost tienen diez ensayos por búsqueda. Se entrega una comparación armonizada con tres rezagos y predicción de diferencias para los seis modelos ajustables, frente a cinco referencias fijas. Diez ensayos corresponden al periodo inicial de TPE y no verifican convergencia adaptativa.

Los presupuestos mayores de los tres árboles se cierran como extensiones pendientes justificadas por alcance. Aumentarlos después de inspeccionar el ranking ampliaría la selección exploratoria y no proporcionaría una confirmación por sí mismo. Los ensayos parciales se conservan fuera del ranking. Esta limitación impide afirmar que se alcanzó la capacidad óptima de esos algoritmos.

## Selección y dependencia

El mínimo de 65 configuraciones está sujeto a optimismo de selección. El bootstrap original por países conserva las trayectorias, pero condiciona a los modelos entrenados. La sensibilidad nueva remuestrea países y bloques de años y toma el máximo de desviaciones absolutas en la familia de 65 configuraciones. Se comparan bloques de uno, dos y tres años. Los intervalos son conservadores e influidos por las configuraciones de mayor variabilidad. Con seis años constituyen sensibilidad descriptiva. No corrigen completamente el proceso de entrenamiento y selección.

## Intervalos no informativos

La calibración por máximos anuales tiene entre dos y seis bloques previos. El rango conformal al 90 % puede superar el número de bloques disponibles. La salida 0–100 % cubre todo el soporte y tiene un ancho de 100 puntos porcentuales. Su cobertura del 100 % es trivial y no informativa. Se conserva como diagnóstico de información insuficiente.

La banda agrupada de persistencia cubrió el 60 % de los países en 2020 y el 55 % en 2021. La dependencia temporal y geográfica, los cambios de régimen y la incertidumbre de las estimaciones fuente requieren revisar la calibración antes del uso operativo.

## Extensión temporal adicional

WDI llega hasta 2021. La API OMS NCDMORT3070 ofrece 2022–2023, con fecha de registro del 15 de octubre de 2026. La edición revisa la historia, de modo que se empleó una serie homogénea de esa fuente. El protocolo se congeló en 1d4cb563423796de4255138efd063ab2d091e534 antes de descargar todos los resultados. Perú se excluyó del análisis principal por haber sido consultado en el sondeo inicial.

Se reajustó Ridge hasta 2021 con alfa congelado del experimento original y se evaluaron pronósticos a un paso en 2022–2023, sin nueva búsqueda. En 38 observaciones de 19 países, el MAE fue 0,62490 pp frente a 0,63158 pp de persistencia. La diferencia fue −0,00668 pp, con IC95 % por países de −0,03987 a 0,02789 pp. Es una extensión retrospectiva temporal y entre ediciones, con limitaciones por revisiones de fuente y solo dos años de evaluación.

La independencia de esta extensión se refiere a la selección del algoritmo y de sus hiperparámetros antes de consultar los resultados completos. La edición de 2026 puede incorporar información posterior al año estimado al revisar la historia. Falta una evaluación con versiones de datos disponibles en cada fecha de emisión y resultados recogidos después de congelar el sistema. Esa limitación impide equiparar la extensión retrospectiva con una validación prospectiva.

## Contradicciones aclaradas

- El histórico PROTOCOLO.md y el puerto 8501 corresponden a tasas por 100 000 y redes neuronales. El artículo auditado usa probabilidad porcentual y métodos tabulares.
- La validación geográfica histórica y el nuevo rolling-origin son análisis diferentes.
- 2019–2021 conserva su condición de periodo previamente examinado.
- El hash 26cc4e…c0d70 identifica la versión LF de Git y a0556b…fcbf6d la copia CRLF de Windows. Los valores coinciden.
- El generador actual y los intervalos recalculados usan full_support_due_to_small_n. Los resultados históricos se conservan.
- La ausencia de años posteriores a 2021 se restringe a WDI. La revisión final encontró una extensión de la OMS.

## Integración continua

GitHub Actions instala las versiones científicas congeladas en Windows con Python 3.12.9. Las acciones externas se fijan por SHA y el token tiene permiso de lectura. El entorno mínimo usa research.requirements.txt restringido por dependencies.lock.txt. clean_environment.lock.txt registra las dependencias realmente resueltas. La reproducción completa de predicciones consta en clean_reproduction.csv.

## Pendientes antes de enviar

Confirmar afiliaciones, ORCID faltantes, contribuciones, financiación y aprobación del texto por los autores. Revalidar las instrucciones vigentes de RPMESP y depositar una versión identificable de los materiales. La repetición integral de toda la búsqueda de Optuna, la portabilidad a otros sistemas y la utilidad operativa de las bandas requieren verificaciones adicionales.

Los presupuestos mayores de tres árboles se reportan como limitación. La comparación de once métodos y las 65 configuraciones no permite concluir superioridad por el solo hecho de obtener el menor MAE observado.
