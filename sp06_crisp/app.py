import hashlib
import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from reporting import build_report, show_bar, show_chart, show_line, show_table
from modeling import FEATURES, prepare, statistical_tests, test_holdout, validate
from visuals import BLUE, COUNTRY_NAMES, correlation_chart, country_map, forecast_chart, shap_importance, shap_values

@st.cache_resource(show_spinner=False)
def trained_run(panel):
    return validate(panel)


st.set_page_config(page_title="SP-06 · CRISP-DM", layout="wide")
workflow = st.sidebar.radio("Versión del estudio", ["Protocolo de siete fases", "CRISP-DM histórico"])
if workflow == "Protocolo de siete fases":
    from workflow import render

    render()
    st.stop()
st.html("""<div style="background:linear-gradient(115deg,#102a43,#087e8b);color:white;
padding:1.7rem 2rem;border-radius:16px;margin-bottom:1.4rem">
<div style="font-size:.85rem;letter-spacing:.12em">SP-06 · OBSERVATORIO DE MORTALIDAD</div>
<h1 style="color:white;padding:.35rem 0">Mortalidad prematura por ENT</h1>
<div>América Latina · Datos públicos OMS / Banco Mundial · Metodología CRISP-DM</div>
</div>""")
dataset = Path(__file__).with_name("wdi_mortality.csv")
fingerprint = hashlib.sha256(dataset.read_bytes()).hexdigest()
data = pd.read_csv(dataset)
development = data[data.year < 2018]
panel = prepare(data)
sections = [
    "1. Problema", "2. Datos y EDA", "3. Preparación", "4. Modelado",
    "5. Evaluación", "6. Uso", "Sustentación",
]
problem, eda, preparation, modeling, evaluation, usage, defense = st.tabs(
    sections, key="study_section", on_change="rerun"
)

country = st.sidebar.selectbox("País de referencia", sorted(data.iso3.unique()),
                               index=sorted(data.iso3.unique()).index("PER"),
                               format_func=COUNTRY_NAMES.get)
st.sidebar.caption("El país se aplica al mapa, la evaluación y el pronóstico.")
if "experiment" not in st.session_state:
    with st.spinner("Preparando el estudio y comparando los modelos"):
        st.session_state.experiment = trained_run(panel)
folds, scores, ranking, winner, search, radius = st.session_state.experiment
if "holdout" not in st.session_state:
    st.session_state.holdout = test_holdout(panel, search, radius)
metrics, predictions = st.session_state.holdout

with problem:
    summary = st.columns(4)
    summary[0].metric("Países", data.iso3.nunique(), border=True)
    summary[1].metric("Modelo ajustado seleccionado", winner, border=True)
    summary[2].metric("MAE en prueba", f"{metrics['MAE (pp)']:.2f} pp", border=True)
    summary[3].metric("MAE de persistencia", f"{metrics['MAE persistencia (pp)']:.2f} pp", border=True)
    if metrics["MAE persistencia (pp)"] < metrics["MAE (pp)"]:
        st.info("En la prueba reservada, persistencia obtuvo un MAE menor que el modelo ajustado seleccionado.")
    st.subheader(f"Resultado en {COUNTRY_NAMES[country]}")
    show_chart("portada", "La distancia entre observado y pronosticado indica el error por año. La banda refleja la dispersión de errores de desarrollo.", forecast_chart(data[data.iso3 == country].tail(12),
                                  predictions[predictions.iso3 == country]), width="stretch")
    st.caption("Prueba reservada 2018–2021. La banda representa incertidumbre exploratoria. "
               "Persistencia repite el último valor observado.")
    st.header("Comprensión del problema")
    st.write("Pronosticar a un año la probabilidad de morir entre los 30 y los 70 años "
             "por las cuatro ENT combinadas. El indicador se expresa en porcentaje.")
    st.write("CRISP-DM organiza el análisis. En la entrega docente, el entrenamiento corresponde "
             "a la fase 2 y se ejecuta desde la pestaña Modelado.")

with eda:
    st.header("Dataset público y análisis exploratorio")
    st.markdown("Estimaciones nacionales de la OMS publicadas por el Banco Mundial. "
                "[Indicador SH.DYN.NCOM.ZS](https://data.worldbank.org/indicator/SH.DYN.NCOM.ZS) · CC BY 4.0.")
    st.caption("Copia descargada el 9 de noviembre de 2026. "
               "El análisis exploratorio usa únicamente el periodo 2000–2017.")
    cols = st.columns(3)
    cols[0].metric("Países", development.iso3.nunique())
    cols[1].metric("Filas de desarrollo", len(development))
    cols[2].metric("Claves país-año duplicadas", int(development.duplicated(["iso3", "year"]).sum()))
    geography, distributions, temporal, quality = st.tabs([
        "Mapa regional", "Distribución", "Series y correlaciones", "Calidad y procedencia",
    ])
    eda_rows = panel[panel.year < 2018]
    with geography:
        year = st.slider("Año del mapa", int(development.year.min()), int(development.year.max()),
                         int(development.year.max()))
        year_rows = development[development.year == year]
        map_col, ranking_col = st.columns([3, 2])
        with map_col:
            show_chart("mapa", "El color representa la probabilidad nacional para el año elegido. El borde oscuro identifica el país de referencia.", country_map(year_rows, country), width="stretch")
            st.caption("Valores nacionales · Cartografía World Atlas / Natural Earth.")
        with ranking_col:
            st.subheader(f"Comparación por país · {year}")
            bars = alt.Chart(year_rows).mark_bar(color=BLUE, cornerRadiusEnd=3).encode(
                y=alt.Y("iso3:N", sort="-x", title=None),
                x=alt.X("probability_pct:Q", title="Probabilidad (%)"),
                tooltip=["iso3", alt.Tooltip("probability_pct:Q", format=".1f")],
            ).properties(height=410)
            show_chart("ranking-paises", "Las barras ordenan a los países según su probabilidad estimada en el año elegido. Son comparaciones descriptivas.", bars, width="stretch")
    with distributions:
        left, right = st.columns(2)
        with left:
            st.subheader("Distribución del indicador")
            histogram = alt.Chart(development).mark_bar(color=BLUE).encode(
                x=alt.X("probability_pct:Q", bin=alt.Bin(maxbins=15), title="Probabilidad (%)"),
                y=alt.Y("count()", title="Observaciones"), tooltip=["count()"],
            )
            show_chart("histograma", "La altura indica cuántas observaciones país-año caen en cada intervalo. El gráfico reúne el periodo de desarrollo.", histogram, width="stretch")
        with right:
            st.subheader("Variación histórica por país")
            boxes = alt.Chart(development).mark_boxplot(color=BLUE).encode(
                x=alt.X("probability_pct:Q", title="Probabilidad (%)"),
                y=alt.Y("iso3:N", title=None),
            ).properties(height=360)
            show_chart("cajas", "La línea central muestra la mediana y la caja contiene la mitad central de los valores históricos de cada país.", boxes, width="stretch")
    with temporal:
        countries = st.multiselect("Países para comparar", sorted(development.iso3.unique()),
                                   default=["PER", "CHL", "COL"], format_func=COUNTRY_NAMES.get)
        series = development[development.iso3.isin(countries)]
        chart = alt.Chart(series).mark_line(point=True).encode(
            x=alt.X("year:O", title="Año"), y=alt.Y("probability_pct:Q", title="Probabilidad (%)"),
            color=alt.Color("iso3:N", title="País"), tooltip=["iso3", "year", "probability_pct"],
        )
        show_chart("series", "Compara la trayectoria de los países elegidos. Cada punto corresponde a una estimación anual.", chart, width="stretch")
        st.subheader("Correlación de Pearson con los rezagos")
        show_chart("correlaciones", "Valores cercanos a 1 indican asociación lineal positiva. Los rezagos comparten la trayectoria temporal del indicador.", correlation_chart(eda_rows[["probability_pct", *FEATURES]]), width="stretch")
    with quality:
        show_table("faltantes", "Cada valor cuenta las celdas vacías en esa columna durante el desarrollo.", development.isna().sum().rename("Faltantes por columna"), width="stretch")
        show_table("descriptivos", "La media y la mediana resumen el nivel típico. Los cuartiles y los extremos muestran la dispersión.", development.probability_pct.describe().rename("Probabilidad (%)"), width="stretch")
        show_table("cobertura", "El mínimo y máximo identifican el primer y último año disponibles. El conteo permite detectar series incompletas.", development.groupby("iso3").year.agg(["min", "max", "count"]), width="stretch")
    st.download_button("Descargar datos de desarrollo", development.to_csv(index=False),
                       "sp06-desarrollo.csv", "text/csv")

with preparation:
    st.header("Preparación")
    periods = pd.DataFrame([
        {"etapa": "Ajuste · 5 folds internos", "inicio": 2003, "fin": 2014},
        {"etapa": "Evaluación · 5 folds externos", "inicio": 2015, "fin": 2017},
        {"etapa": "Prueba final reservada", "inicio": 2018, "fin": 2021},
    ])
    show_chart("cronograma", "Cada barra indica los años objetivo de una etapa. La prueba final se reserva para medir desempeño.", alt.Chart(periods).mark_bar(size=16, cornerRadius=4).encode(
        x=alt.X("inicio:Q", title="Año objetivo", scale=alt.Scale(domain=[2002, 2022]),
                axis=alt.Axis(format="d", tickMinStep=1)),
        x2="fin:Q", y=alt.Y("etapa:N", sort=None, title=None),
        color=alt.Color("etapa:N", legend=None), tooltip=["etapa", "inicio", "fin"],
    ).properties(height=125), width="stretch")
    st.write("Cada fila utiliza los tres años anteriores del mismo país como predictores. "
             "Se excluyen filas sin los tres rezagos consecutivos. El objetivo es log(1 + probabilidad porcentual).")
    st.write("Los años 2018–2021 quedan reservados para la prueba final. "
             "En esa prueba se simula un pronóstico a un año con el historial observado hasta el año anterior.")
    show_table("rezagos", "Cada fila combina el valor objetivo del año con los tres años anteriores del mismo país.", eda_rows[["iso3", "year", *FEATURES, "target"]].head(20), hide_index=True)

with modeling:
    st.header("Entrenamiento en Python")
    st.write("Ridge, Random Forest y XGBoost. Cinco folds externos agrupan países completos, "
             "que son la unidad geográfica disponible. En cada fold, el ajuste usa datos anteriores "
             "a 2015 y la evaluación externa usa 2015–2017 en países separados.")
    st.write("GridSearchCV utiliza cinco folds internos agrupados por país dentro del conjunto "
             "de entrenamiento de cada fold externo.")
    if st.button("Entrenar y comparar modelos", type="primary"):
        with st.spinner("Ejecutando validación cruzada anidada"):
            trained_run.clear()
            st.session_state.experiment = trained_run(panel)
            st.session_state.pop("holdout", None)
            st.session_state.pop("shap_importance", None)
            st.session_state.pop("local_shap", None)
            st.session_state.pop("report", None)
            st.rerun()
    if "experiment" in st.session_state:
        folds, scores, ranking, winner, search, radius = st.session_state.experiment
        st.success(f"Modelo ajustado seleccionado por menor MAE log externo medio · {winner}")
        left, right = st.columns(2)
        with left:
            st.subheader("Rendimiento medio")
            show_bar("ranking-modelos", "Un MAE log menor indica menos error externo. Persistencia usa el último valor observado como referencia.", ranking.rename("MAE log").reset_index(), x="modelo", y="MAE log", color=BLUE)
        with right:
            st.subheader("Error por fold externo")
            show_line("error-fold", "La variación entre puntos muestra cuánto cambia el error entre grupos de países.", scores, x="fold", y="MAE log", color="modelo", x_label="Fold")
        with st.expander("Países por fold e hiperparámetros seleccionados"):
            show_table("folds", "Cada fila identifica los países evaluados y el número de observaciones usadas en el fold externo.", folds, hide_index=True)
            show_table("hiperparametros", "La tabla muestra la configuración elegida por la búsqueda interna y el error obtenido en cada fold externo.", scores, hide_index=True)
        st.subheader("SHAP · Importancia de los rezagos")
        st.caption("Atribuciones globales en la escala logarítmica del modelo ganador, calculadas "
                   "sobre el conjunto de desarrollo. Las atribuciones describen el modelo y su magnitud.")
        if st.button("Calcular SHAP"):
            with st.spinner("Calculando atribuciones"):
                st.session_state.shap_importance = shap_importance(search, eda_rows, FEATURES)
        if "shap_importance" in st.session_state:
            show_bar("shap-global", "Las barras muestran la magnitud media de los aportes en escala logarítmica. Un valor mayor indica mayor influencia en el modelo.", st.session_state.shap_importance, x="Rezago", y="SHAP medio absoluto",
                         horizontal=True, color=BLUE)


with evaluation:
    st.header("Evaluación y pruebas estadísticas")
    if "experiment" not in st.session_state:
        st.info("Primero ejecuta el entrenamiento.")
    else:
        show_table("mae-externo", "La tabla promedia el MAE log de los cinco folds externos para cada modelo.", ranking.rename("MAE log externo medio"))
        friedman, pairs = statistical_tests(scores)
        st.write(f"Friedman · estadístico {friedman.statistic:.4g} · p = {friedman.pvalue:.4g}")
        show_table("pruebas-estadisticas", "Los valores p corregidos por Holm se interpretan de forma exploratoria con cinco folds.", pairs, hide_index=True)
        st.caption("Wilcoxon compara errores pareados por fold. Holm corrige las comparaciones múltiples. "
                   "Shapiro–Wilk se aplica a las diferencias pareadas. Con cinco folds y conjuntos "
                   "de entrenamiento solapados, la interpretación es exploratoria.")
        st.subheader("Prueba reservada · 2018–2021")
        columns = st.columns(len(metrics))
        for column, (name, value) in zip(columns, metrics.items()):
            column.metric(name, f"{value:.3f}")
        show_chart("prueba-grafico", "Compara los valores observados, el modelo ajustado y la persistencia para el país seleccionado.", forecast_chart(data[data.iso3 == country].tail(12),
                                      predictions[predictions.iso3 == country]), width="stretch")
        st.caption(f"Banda exploratoria al 90 % nominal, con radio ±{radius:.2f} pp. "
                   "Se estima con errores de los folds externos del modelo seleccionado.")
        if "holdout" in st.session_state:
            residuals = predictions.assign(residuo=predictions.probability_pct - predictions["pronóstico"])
            show_chart("residuos", "Un residuo positivo indica que el modelo subestimó el valor observado. La dispersión muestra dónde varía el error.", alt.Chart(residuals).mark_circle(color=BLUE, opacity=0.55).encode(
                x=alt.X("pronóstico:Q", title="Pronóstico (%)"),
                y=alt.Y("residuo:Q", title="Error observado − pronosticado (pp)"),
                tooltip=["iso3", "year", "residuo"],
            ).properties(height=260), width="stretch")
            with st.expander("Predicciones de prueba"):
                show_table("prueba-tabla", "Cada fila muestra el valor observado, los dos pronósticos y los límites exploratorios para un país y año.", predictions, hide_index=True)

with usage:
    st.header("Uso del modelo entrenado")
    if "experiment" not in st.session_state:
        st.info("Entrena para pronosticar el siguiente año de un país.")
    else:
        selected = country
        last_three = data[data.iso3 == selected].sort_values("year").tail(3)
        features = pd.DataFrame([last_three.probability_pct.to_numpy()[::-1]], columns=FEATURES)
        forecast = float(np.expm1(search.predict(features)[0]).clip(0, 100))
        year = int(last_three.year.max()) + 1
        st.metric(f"{COUNTRY_NAMES[selected]} · {year}", f"{forecast:.2f} %")
        st.caption(f"Banda exploratoria · {max(0, forecast - radius):.2f} a {min(100, forecast + radius):.2f} %")
        future = pd.DataFrame({"year": [year], "pronóstico": [forecast],
                               "persistencia": [last_three.probability_pct.iloc[-1]],
                               "inferior": [max(0, forecast - radius)], "superior": [min(100, forecast + radius)]})
        show_chart("pronostico", "El último punto corresponde al pronóstico a un año. La barra vertical marca su rango exploratorio.", forecast_chart(data[data.iso3 == selected].tail(10), future), width="stretch")
        if st.button("Explicar este pronóstico con SHAP"):
            contributions = shap_values(search, eda_rows[FEATURES], features)[0]
            st.session_state.local_shap = (selected, contributions)
        local = st.session_state.get("local_shap")
        if local is not None and local[0] == selected:
            impacts = pd.DataFrame({"Rezago": FEATURES, "Aporte": local[1]})
            show_chart("shap-local", "Los aportes positivos elevan el resultado en escala logarítmica y los negativos lo reducen respecto al valor base.", alt.Chart(impacts).mark_bar().encode(
                x=alt.X("Aporte:Q", title="Aporte a log(1 + probabilidad)"),
                y=alt.Y("Rezago:N", title=None),
                color=alt.condition(alt.datum.Aporte >= 0, alt.value(BLUE), alt.value("#bd6b26")),
                tooltip=["Rezago", alt.Tooltip("Aporte:Q", format=".4f")],
            ).properties(height=170), width="stretch")
        st.caption(f"Modelo {winner} ajustado hasta 2017. Pronóstico a un año con rezagos observados hasta "
                   f"{last_three.year.max()}. Modelo disponible durante la sesión.")
        if "holdout" in st.session_state:
            st.download_button("Descargar evaluación reservada", predictions.to_csv(index=False),
                               "sp06-prueba-2018-2021.csv", "text/csv")

        report = {
            "fuente": "https://data.worldbank.org/indicator/SH.DYN.NCOM.ZS",
            "dataset_sha256": fingerprint,
            "modelo_ajustado": winner,
            "hiperparámetros": search.best_params_,
            "folds_externos": folds.to_dict("records"),
            "resultados_por_fold": scores.to_dict("records"),
            "prueba_reservada": {"años": [2018, 2021], "métricas": metrics},
            "radio_exploratorio_pp": radius,
            "limitaciones": ["Estimaciones nacionales de la OMS publicadas por el Banco Mundial",
                             "Validación geográfica por países completos", "Bandas exploratorias"],
        }
        st.download_button("Descargar ficha reproducible de la corrida",
                           json.dumps(report, ensure_ascii=False, indent=2),
                           "sp06-ficha-corrida.json", "application/json")

with usage:
    st.subheader("Reportes del estudio")
    st.caption("El reporte reúne procedencia, resultados de validación, prueba reservada y el gráfico del país seleccionado.")
    report_format = st.selectbox("Formato del reporte", ["PDF", "Word", "Excel"])
    report_key = (fingerprint, country, report_format)
    if st.button("Preparar reporte"):
        with st.spinner("Generando el reporte"):
            chart = forecast_chart(data[data.iso3 == country].tail(12), predictions[predictions.iso3 == country])
            st.session_state.report = (report_key, build_report(
                report_format, COUNTRY_NAMES[country], report, metrics, folds, scores, predictions, chart
            ))
    prepared_report = st.session_state.get("report")
    if prepared_report is not None and prepared_report[0] == report_key:
        payload, extension, mime = prepared_report[1]
        st.download_button(f"Descargar reporte {report_format}", payload, f"sp06-{country}.{extension}", mime)

with defense:
    st.header("Sustentación del proyecto SP-06")
    st.write("Usa este recorrido para presentar el problema, mostrar la evidencia y cerrar con el pronóstico y los reportes.")
    topics = [
        ("Objetivo y resultado principal", "Pregunta de investigación, indicador y caso del país seleccionado."),
        ("Datos públicos y EDA", "Procedencia OMS/Banco Mundial, mapa regional, distribuciones, series, correlaciones y calidad."),
        ("Preparación y diseño de validación", "Tres rezagos por país, transformación del objetivo y línea de tiempo de la prueba reservada."),
        ("Entrenamiento y SHAP global", "Comparación de modelos y persistencia, cinco folds externos, GridSearchCV con cinco internos e importancia de rezagos."),
        ("Prueba final y evidencia estadística", "Métricas, cobertura, residuos y pruebas exploratorias de Friedman, Wilcoxon con Holm y Shapiro–Wilk."),
        ("Pronóstico, SHAP local y reportes", "Pronóstico a un año, explicación por país y descarga en PDF, Word o Excel."),
    ]
    for number, (title, description) in enumerate(topics, start=1):
        with st.container(border=True):
            content_col, link_col = st.columns([3, 1])
            content_col.markdown(f"**{number}. {title}**")
            content_col.write(description)
            link_col.button(f"Ir a {sections[number - 1].split('. ', 1)[1]}",
                            key=f"defense_link_{number}", width="stretch",
                            on_click=st.session_state.__setitem__,
                            args=("study_section", sections[number - 1]))
    st.caption("Los gráficos y las tablas incluyen interpretabilidad, explicación y descarga. "
               "La validación geográfica agrupa países completos y la banda de pronóstico es exploratoria.")
