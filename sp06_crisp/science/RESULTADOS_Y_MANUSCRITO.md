# Resultados exploratorios y propuesta para el manuscrito RPMESP

Versión del análisis exploratorio de 65 configuraciones. La revisión editorial
final y la nueva extensión de la OMS se documentan en
[final_audit/INFORME_FINAL.md](final_audit/INFORME_FINAL.md). La consulta de
disponibilidad temporal citada aquí corresponde a WDI.

Estos resultados corresponden a seis orígenes externos anuales, 2013–2018, con 20 países por origen. Los intervalos remuestrean países y están condicionados a los modelos y a la búsqueda realizada. Las configuraciones se eligieron después de comparar múltiples experimentos exploratorios.

| Método y configuración exploratoria | MAE pp | RMSE pp | MASE | Δ frente a persistencia | IC95 % | Países con menor error |
| --- | --- | --- | --- | --- | --- | --- |
| Ridge-lag5-difference-60 | 0.3076 | 0.4192 | 0.981 | -0.0091 | [-0.0265, 0.0066] | 50 % |
| HistGradientBoosting-lag5-difference-10 | 0.3080 | 0.4261 | 0.985 | -0.0086 | [-0.0297, 0.0089] | 55 % |
| Elastic Net-lag5-difference-30 | 0.3105 | 0.4226 | 0.990 | -0.0062 | [-0.0230, 0.0088] | 55 % |
| Persistencia-lag3-level-0 | 0.3167 | 0.4181 | 1.019 | 0.0000 | [0.0000, 0.0000] | 0 % |
| CatBoost-lag3-difference-10 | 0.3198 | 0.4261 | 1.012 | 0.0031 | [-0.0195, 0.0248] | 50 % |
| XGBoost-lag3-difference-10 | 0.3216 | 0.4343 | 1.020 | 0.0049 | [-0.0195, 0.0288] | 40 % |
| Deriva amortiguada-lag3-level-0 | 0.3218 | 0.4306 | 1.019 | 0.0051 | [-0.0215, 0.0321] | 45 % |
| Random Forest-lag3-difference-10 | 0.3224 | 0.4307 | 1.028 | 0.0057 | [-0.0229, 0.0312] | 50 % |
| ARIMA-lag3-level-0 | 0.3234 | 0.4615 | 1.026 | 0.0068 | [-0.0335, 0.0553] | 35 % |
| ETS-lag3-level-0 | 0.3581 | 0.5571 | 1.106 | 0.0415 | [-0.0164, 0.1160] | 45 % |
| Media móvil-lag3-level-0 | 0.4375 | 0.5926 | 1.355 | 0.1208 | [0.0444, 0.2114] | 15 % |

## Redacción propuesta basada en la ejecución

Se compararon 65 configuraciones completas mediante validación temporal anidada. El menor MAE observado en la búsqueda exploratoria fue 0.3076 puntos porcentuales para Ridge-lag5-difference-60. La diferencia media frente a persistencia fue -0.0091 pp, con intervalo percentil del 95 % de -0.0265 a 0.0066 pp. El método tuvo menor error en 50 % de los países. El resultado requiere confirmación con datos independientes de esta búsqueda.

## Cambios del manuscrito

Describir 2019–2021 como un periodo previamente examinado. Documentar la distinción entre el protocolo histórico por país y el nuevo backtest temporal. Incluir los resultados de persistencia en todas las comparaciones. Explicar la diferencia entre el hash de los bytes CRLF y el archivo LF publicado en Git. Presentar los rangos y el número de ensayos realmente completados. Reemplazar las atribuciones de superioridad general por la diferencia de error, su intervalo y su estabilidad por país.

## Limitaciones y pendientes

Los presupuestos de 30 y 60 para Random Forest, XGBoost y CatBoost quedan pendientes. La evaluación de covariables externas requiere versiones y fechas de publicación antes de incorporarlas a una ablación. Los años posteriores a 2021 siguen sin estar disponibles en la consulta del indicador para los 20 países. Las bandas por bloque anual tienen pocos años de calibración. El bootstrap de países no corrige la selección de la mejor configuración entre múltiples experimentos. La comparación aísla tipos de variables y objetivo, pero no establece causalidad.

## Archivos

comparison.csv contiene las métricas y la procedencia por experimento. predictions.csv de cada lote conserva todos los país-año y parámetros por origen. coverage_by_year.csv y coverage_by_iso3.csv presentan la calibración en desarrollo. Los gráficos model_comparison y budget_comparison se entregan en PNG y HTML.

## Sensibilidad retrospectiva de persistencia en 2020–2021

| Calibración | Año | Cobertura | Ancho pp |
| --- | --- | --- | --- |
| empirical | 2020 | 60 % | 1.200 |
| empirical | 2021 | 55 % | 1.400 |
| pooled_conformal | 2020 | 60 % | 1.200 |
| pooled_conformal | 2021 | 55 % | 1.400 |
| year_block_conformal | 2020 | 100 % | 100.000 |
| year_block_conformal | 2021 | 100 % | 100.000 |

Los rangos que cubren todo 0–100 % señalan insuficiencia de bloques para una banda conformal finita. Los resultados de este periodo son una sensibilidad retrospectiva y se conservan fuera del ranking de desarrollo.
