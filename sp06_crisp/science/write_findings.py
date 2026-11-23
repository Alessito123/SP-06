from pathlib import Path
import json
import pandas as pd
root=Path(__file__).parent
d=pd.read_csv(root/"comparison.csv")
best=d.iloc[0]
rows=d.loc[d.groupby("model").MAE.idxmin()].sort_values("MAE")
lines=["# Resultados exploratorios y propuesta para el manuscrito RPMESP","",
"Estos resultados corresponden a seis orígenes externos anuales, 2013–2018, con 20 países por origen. "
"Los intervalos remuestrean países y están condicionados a los modelos y a la búsqueda realizada. "
"Las configuraciones se eligieron después de comparar múltiples experimentos exploratorios.","",
"| Método y configuración exploratoria | MAE pp | RMSE pp | MASE | Δ frente a persistencia | IC95 % | Países con menor error |",
"| --- | --- | --- | --- | --- | --- | --- |"]
for row in rows.itertuples():
 lines.append(f"| {row.experiment} | {row.MAE:.4f} | {row.RMSE:.4f} | {row.MASE:.3f} | {row.delta_MAE:.4f} | [{row.CI_lower:.4f}, {row.CI_upper:.4f}] | {row.countries_better_pct:.0f} % |")
lines+=["","## Redacción propuesta basada en la ejecución","",
f"Se compararon {len(d)} configuraciones completas mediante validación temporal anidada. "
f"El menor MAE observado en la búsqueda exploratoria fue {best.MAE:.4f} puntos porcentuales "
f"para {best.experiment}. La diferencia media frente a persistencia fue {best.delta_MAE:.4f} pp, "
f"con intervalo percentil del 95 % de {best.CI_lower:.4f} a {best.CI_upper:.4f} pp. "
f"El método tuvo menor error en {best.countries_better_pct:.0f} % de los países. "
"El resultado requiere confirmación con datos independientes de esta búsqueda.",
"",
"## Cambios del manuscrito",
"",
"Describir 2019–2021 como un periodo previamente examinado. Documentar la distinción entre el protocolo histórico por país "
"y el nuevo backtest temporal. Incluir los resultados de persistencia en todas las comparaciones. "
"Explicar la diferencia entre el hash de los bytes CRLF y el archivo LF publicado en Git. "
"Presentar los rangos y el número de ensayos realmente completados. "
"Reemplazar las atribuciones de superioridad general por la diferencia de error, su intervalo y su estabilidad por país.",
"",
"## Limitaciones y pendientes",
"",
"Los presupuestos de 30 y 60 para Random Forest, XGBoost y CatBoost quedan pendientes. "
"La evaluación de covariables externas requiere versiones y fechas de publicación antes de incorporarlas a una ablación. "
"Los años posteriores a 2021 siguen sin estar disponibles en la consulta del indicador para los 20 países. "
"Las bandas por bloque anual tienen pocos años de calibración. "
"El bootstrap de países no corrige la selección de la mejor configuración entre múltiples experimentos. "
"La comparación aísla tipos de variables y objetivo, pero no establece causalidad.",
"",
"## Archivos",
"",
"comparison.csv contiene las métricas y la procedencia por experimento. predictions.csv de cada lote conserva todos los "
"país-año y parámetros por origen. coverage_by_year.csv y coverage_by_iso3.csv presentan la calibración en desarrollo. "
"Los gráficos model_comparison y budget_comparison se entregan en PNG y HTML."]
examined=pd.read_csv(root/"examined_baselines/intervals.csv")
coverage=examined.query("experiment == 'Persistencia-lag3-level-0'").groupby(["method","year"]).agg(
 coverage=("coverage","mean"),width=("width","mean")).reset_index()
coverage.to_csv(root/"examined_coverage.csv",index=False)
lines+=["","## Sensibilidad retrospectiva de persistencia en 2020–2021","",
"| Calibración | Año | Cobertura | Ancho pp |","| --- | --- | --- | --- |"]
for row in coverage[coverage.year>=2020].itertuples():
 lines.append(f"| {row.method} | {row.year} | {100*row.coverage:.0f} % | {row.width:.3f} |")
lines+=["","Los rangos que cubren todo 0–100 % señalan insuficiencia de bloques para una banda conformal finita. "
"Los resultados de este periodo son una sensibilidad retrospectiva y se conservan fuera del ranking de desarrollo."]
(root/"RESULTADOS_Y_MANUSCRITO.md").write_text("\n".join(lines),encoding="utf8")
print("\n".join(lines[:15]))
