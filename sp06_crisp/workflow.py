"""Streamlit views for the seven-phase forecasting protocol."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from engine import forecast, list_runs, load_run, save_run
from modeling import FEATURES, statistical_tests
from protocol_v2 import SPACES, calibrate, evaluate_nested, read_data, split_panel
from reporting import build_report, show_bar, show_chart, show_line, show_table
from visuals import BLUE, COUNTRY_NAMES, correlation_chart, country_map, forecast_chart, shap_importance, shap_values

SOURCE = "https://data.worldbank.org/indicator/SH.DYN.NCOM.ZS"
PHASES = [
    "1. Datos y EDA", "2. Entrenamiento", "3. Evaluación", "4. Explicabilidad",
    "5. Reportes", "6. Motor", "7. Optuna", "Sustentación",
]


def country_name(code):
    return COUNTRY_NAMES.get(code, code)


def evaluate_test(model, manifest, test, development, seed):
    predicted = model.predict(test[FEATURES])
    rows = test[["iso3", "year", "probability_pct"]].copy()
    rows["pronóstico"] = np.expm1(predicted).clip(0, 100)
    rows["persistencia"] = test.lag1
    rows["inferior"] = (rows["pronóstico"] - manifest["radius"]).clip(0, 100)
    rows["superior"] = (rows["pronóstico"] + manifest["radius"]).clip(0, 100)
    actual = rows.probability_pct
    error = abs(actual - rows["pronóstico"])
    baseline = abs(actual - rows.persistencia)
    by_country = rows.assign(delta=error - baseline).groupby("iso3").delta.mean()
    rng = np.random.default_rng(seed)
    sampled = rng.choice(by_country.to_numpy(), size=(5000, len(by_country))).mean(axis=1)
    interval = np.quantile(sampled, [0.025, 0.975])
    metrics = {
        "MAE log": mean_absolute_error(test.target, predicted),
        "MAE (pp)": float(error.mean()),
        "RMSE (pp)": root_mean_squared_error(actual, rows["pronóstico"]),
        "MAE persistencia (pp)": float(baseline.mean()),
        "Cobertura (%)": float(100 * actual.between(rows.inferior, rows.superior).mean()),
        "Ancho medio (pp)": float((rows.superior - rows.inferior).mean()),
        "Diferencia por país (pp)": float(by_country.mean()),
        "IC95 % inferior (pp)": float(interval[0]),
        "IC95 % superior (pp)": float(interval[1]),
    }
    scales = (development.probability_pct - development.lag1).abs().groupby(development.iso3).mean()
    denominators = rows.iso3.map(scales)
    defined = denominators.gt(0)
    if defined.any():
        metrics["MASE"] = float((error[defined] / denominators[defined]).mean())
    return metrics, rows


def read_metadata(fingerprint, public):
    values = {
        "publisher": "Banco Mundial" if public else "",
        "source": SOURCE if public else "",
        "license": "CC BY 4.0" if public else "",
        "retrieved": "2026-11-09" if public else "",
        "edition": "WDI · SH.DYN.NCOM.ZS" if public else "",
        "inclusion": "Estimaciones nacionales anuales para ambos sexos." if public else "",
    }
    labels = {
        "publisher": "Entidad publicadora", "source": "URL de procedencia",
        "license": "Licencia", "retrieved": "Fecha de descarga", "edition": "Versión",
        "inclusion": "Criterios de inclusión",
    }
    with st.expander("Editar y descargar la ficha del dataset"):
        for key, label in labels.items():
            values[key] = st.text_input(label, values[key], key=f"{fingerprint}-{key}", max_chars=300)
        metadata = {**values, "indicator": "SH.DYN.NCOM.ZS", "unit": "%", "sha256": fingerprint}
        st.download_button("Descargar ficha JSON", json.dumps(metadata, ensure_ascii=False, indent=2),
                           "sp06-procedencia.json", "application/json")
    return metadata


def show_eda(data, calendar, blocks, country):
    development = data[data.year.isin(calendar["Desarrollo"])]
    st.caption("El análisis exploratorio se limita al bloque de desarrollo.")
    audit = pd.DataFrame([
        {"Indicador": "Duplicados país-año", "Conteo": int(development.duplicated(["iso3", "year"]).sum())},
        {"Indicador": "Celdas vacías", "Conteo": int(development.isna().sum().sum())},
        {"Indicador": "Combinaciones país-año ausentes",
         "Conteo": len(calendar["Desarrollo"]) * development.iso3.nunique() - len(development)},
        {"Indicador": "Filas sin tres rezagos", "Conteo": len(development) - len(blocks["Desarrollo"])},
    ])
    show_table("faltantes", "La auditoría distingue celdas vacías, claves ausentes y filas excluidas al crear rezagos.",
               audit, hide_index=True)
    coverage = development.groupby("iso3").year.agg(["min", "max", "count"])
    show_table("cobertura", "La cobertura identifica países con menos años de los esperados.", coverage)
    geography, distribution, series = st.tabs(["Geografía", "Distribución", "Series y correlaciones"])
    with geography:
        year = st.select_slider("Año del mapa", options=calendar["Desarrollo"], value=calendar["Desarrollo"][-1])
        rows = development[development.year == year]
        if rows.iso3.isin(COUNTRY_NAMES).any():
            show_chart("mapa", "El color representa la probabilidad del año elegido en los países con cartografía incluida.",
                       country_map(rows, country), width="stretch")
        ranking = rows.assign(País=rows.iso3.map(country_name))
        show_bar("ranking-paises", "Comparación descriptiva de las estimaciones nacionales de ese año.",
                 ranking, x="País", y="probability_pct", horizontal=True, color=BLUE)
    with distribution:
        chart = alt.Chart(development).mark_bar(color=BLUE).encode(
            x=alt.X("probability_pct:Q", bin=alt.Bin(maxbins=16), title="Probabilidad (%)"),
            y=alt.Y("count()", title="Observaciones"), tooltip=["count()"],
        )
        show_chart("histograma", "Cada barra cuenta observaciones de desarrollo por rango de probabilidad.", chart,
                   width="stretch")
        boxes = alt.Chart(development.assign(País=development.iso3.map(country_name))).mark_boxplot(color=BLUE).encode(
            x=alt.X("probability_pct:Q", title="Probabilidad (%)"), y=alt.Y("País:N", title=None)
        )
        show_chart("cajas", "La caja cubre los cuartiles 1 a 3 y la línea central muestra la mediana.", boxes,
                   width="stretch")
        show_table("descriptivos", "Resumen del nivel y la dispersión en desarrollo.",
                   development.probability_pct.describe().rename("Probabilidad (%)"))
    with series:
        available = sorted(development.iso3.unique())
        selection = st.multiselect("Países", available, default=[country] if country in available else [],
                                   format_func=country_name)
        series_rows = development[development.iso3.isin(selection)].assign(
            País=lambda rows: rows.iso3.map(country_name)
        )
        show_line("series", "Cada punto es una estimación anual de la fuente pública o del panel importado.",
                  series_rows, x="year", y="probability_pct", color="País", x_label="Año")
        show_chart("correlaciones", "La correlación describe asociación lineal dentro del conjunto de desarrollo.",
                   correlation_chart(blocks["Desarrollo"][["probability_pct", *FEATURES]]), width="stretch")
    st.download_button("Descargar datos de desarrollo", development.to_csv(index=False),
                       "sp06-desarrollo.csv", "text/csv")


def configure_search():
    with st.form("v2_optuna"):
        profile = st.radio("Perfil", ["Demostración", "Estudio"], horizontal=True)
        models = st.multiselect("Modelos ajustables", list(SPACES), default=list(SPACES))
        trials = st.number_input("Trials por búsqueda · 0 usa el valor del perfil", min_value=0, max_value=60, value=0)
        seed = st.number_input("Semilla", min_value=0, max_value=2**32 - 1, value=606)
        timeout = st.number_input("Límite por búsqueda (segundos)", min_value=10, max_value=600, value=60)
        spaces = {}
        with st.expander("Rangos de hiperparámetros"):
            for model, parameters in SPACES.items():
                st.markdown(f"**{model}**")
                spaces[model] = {}
                for key, (low, high, kind) in parameters.items():
                    limits = st.slider(f"{model} · {key}", min_value=low, max_value=high, value=(low, high))
                    spaces[model][key] = (*limits, kind)
        submitted = st.form_submit_button("Guardar configuración de Optuna")
    if submitted or "v2_settings" not in st.session_state:
        if not models:
            st.error("Selecciona al menos un modelo ajustable.")
        else:
            st.session_state.v2_settings = {
                "models": models, "trials": int(trials) or (3 if profile == "Demostración" else 24),
                "seed": int(seed), "timeout": int(timeout), "spaces": spaces,
            }
    return st.session_state.v2_settings


def render():
    st.html("""<div style="background:linear-gradient(115deg,#102a43,#087e8b);color:white;
padding:1.5rem 2rem;border-radius:16px;margin-bottom:1rem">
<div style="font-size:.85rem;letter-spacing:.12em">SP-06 · OBSERVATORIO DE MORTALIDAD</div>
<h1 style="color:white;padding:.3rem 0">Mortalidad prematura por ENT</h1>
<div>Protocolo de siete fases · Pronóstico nacional a un año</div>
</div>""")
    st.markdown("[Indicador SH.DYN.NCOM.ZS · OMS y Banco Mundial](https://data.worldbank.org/indicator/SH.DYN.NCOM.ZS)")
    data_tab, training, evaluation, explanation, reports, motor, optimization, defense = st.tabs(
        PHASES, key="v2_section", on_change="rerun"
    )
    with data_tab:
        st.header("Datos públicos y análisis exploratorio")
        upload = st.file_uploader("Importar panel armonizado (CSV)", type=["csv"], max_upload_size=2)
        raw = upload.getvalue() if upload else Path(__file__).with_name("wdi_mortality.csv").read_bytes()
        fingerprint = hashlib.sha256(raw).hexdigest()
        try:
            data = read_data(raw)
            calendar, blocks = split_panel(data)
        except (ValueError, UnicodeError) as error:
            st.error(str(error))
            return
        metadata = read_metadata(fingerprint, upload is None)
        country = st.sidebar.selectbox("País de referencia", sorted(data.iso3.unique()),
                                       index=sorted(data.iso3.unique()).index("PER") if "PER" in set(data.iso3) else 0,
                                       format_func=country_name)
        show_eda(data, calendar, blocks, country)
    with optimization:
        st.header("Configuración de Optuna")
        settings = configure_search()
        st.info(f"Configuración activa · {settings['trials']} trials por búsqueda.")
        launch_optuna = st.button("Iniciar búsqueda y guardar corrida")
        optuna_status = st.empty()
    with training:
        st.header("Entrenamiento y selección")
        st.caption("Cinco folds externos por país con corte temporal y tres folds internos agrupados por país.")
        split = pd.DataFrame([
            {"Etapa": name, "Inicio": years[0], "Fin": years[-1], "Años": len(years),
             "% años": round(100 * len(years) / sum(map(len, calendar.values())), 1),
             "País-año elegibles": len(blocks[name])}
            for name, years in calendar.items()
        ])
        show_table("particion", "El calendario usa años enteros. Los conteos elegibles excluyen filas sin tres rezagos.",
                   split, hide_index=True)
        st.write(f"Modelos activos · Persistencia, {', '.join(settings['models'])}")
        if st.button("Entrenar y guardar corrida", type="primary") or launch_optuna:
            meter = st.progress(0, text="Iniciando validación anidada")
            started = time.monotonic()

            def progress(done, total, last):
                elapsed = time.monotonic() - started
                best = last["mejor MAE log"]
                message = (f"Fold {last['fold']} · {last['modelo']} · trial {last['trial']} · "
                           f"{last['estado']} · {elapsed:.1f} s")
                if best is not None:
                    message += f" · mejor MAE log {best:.4f}"
                meter.progress(min(done / total, 1.0), text=message)
                optuna_status.progress(min(done / total, 1.0), text=message)

            try:
                model, winner, params, folds, scores, trials = evaluate_nested(
                    blocks["Desarrollo"], settings, progress
                )
                radius = calibrate(model, blocks["Validación"])
                run = save_run(model, {
                    "created": datetime.now(timezone.utc).isoformat(), "model": winner,
                    "params": params, "cutoff": calendar["Desarrollo"][-1], "radius": radius,
                    "calendar": calendar, "dataset_sha256": fingerprint, "source": metadata,
                    "settings": settings,
                }, {"folds": folds, "scores": scores, "trials": trials})
            except (ValueError, RuntimeError, OSError) as error:
                meter.empty()
                st.error(f"La corrida no se completó. {error}")
                optuna_status.error(f"La búsqueda no se completó. {error}")
            else:
                meter.progress(1.0, text="Corrida guardada")
                st.session_state.pending_run = run
                st.rerun()
        runs = list_runs(fingerprint)
        if "pending_run" in st.session_state:
            st.session_state[f"run-{fingerprint}"] = st.session_state.pop("pending_run")
        run = st.selectbox("Corrida guardada", [item["id"] for item in runs],
                           key=f"run-{fingerprint}", placeholder="Entrena para guardar una corrida")
        if run:
            try:
                model, manifest, tables = load_run(run)
            except (ValueError, OSError, RuntimeError) as error:
                st.error(f"No se pudo cargar la corrida. {error}")
                run = None
        if run:
            st.success(f"Modelo ajustado seleccionado · {manifest['model']}")
            st.caption(f"Corrida {run} · ajuste hasta {manifest['cutoff']}")
            show_table("folds", "Los países de ajuste y de evaluación externa son disjuntos en cada fold.",
                       tables["folds"], hide_index=True)
            show_table("hiperparametros", "Optuna elige los hiperparámetros con tres folds internos. "
                       "La columna MAE log corresponde a la evaluación externa de ese ajuste.",
                       tables["scores"], hide_index=True)
    if not run:
        for section in (evaluation, explanation, reports, motor):
            section.info("Entrena o selecciona una corrida guardada en la fase 2.")
    else:
        show_run(data, calendar, blocks, country, model, manifest, tables,
                 evaluation, explanation, reports, motor, optimization)

    with defense:
        st.header("Sustentación del proyecto")
        descriptions = [
            "Fuente, metadatos, cobertura, geografía y análisis descriptivo.",
            "Cortes cronológicos, validación anidada y modelo guardado.",
            "Métricas, referencia de persistencia, prueba temporal y contrastes.",
            "Atribuciones SHAP globales y locales.",
            "PDF, Word, Excel y descargas para el manuscrito.",
            "Pronóstico reproducible por país y año sin volver a entrenar.",
            "Configuración, trazas de trials y resultados de búsqueda.",
        ]
        for phase, description in zip(PHASES, descriptions):
            with st.container(border=True):
                left, right = st.columns([3, 1])
                left.markdown(f"**{phase}**")
                left.write(description)
                right.button(f"Abrir fase {phase[0]}", width="stretch", on_click=st.session_state.__setitem__,
                             args=("v2_section", phase))


def show_run(data, calendar, blocks, country, model, manifest, tables,
             evaluation, explanation, reports, motor, optimization):
    run = manifest["id"]
    scores = tables["scores"]
    ranking = scores.groupby("modelo")["MAE log"].mean().sort_values().reset_index()
    test_key = f"v2-test-{run}"
    with evaluation:
        st.header("Evaluación temporal y geográfica")
        show_bar("ranking-modelos", "Un MAE log menor indica menor error medio en los folds externos.",
                 ranking, x="modelo", y="MAE log", color=BLUE)
        show_line("error-fold", "Cada punto corresponde a una evaluación externa por modelo.",
                  scores, x="fold", y="MAE log", color="modelo", x_label="Fold externo")
        if scores.modelo.nunique() >= 3:
            friedman, pairs = statistical_tests(scores)
            st.write(f"Friedman exploratorio · p = {friedman.pvalue:.4f}")
            show_table("pruebas-estadisticas", "Folds con ajuste solapado y muestra pequeña. "
                       "Los valores p se interpretan de forma exploratoria.", pairs, hide_index=True)
        else:
            st.info("Friedman requiere al menos tres comparadores.")
        if st.button("Abrir prueba reservada", type="primary", disabled=test_key in st.session_state):
            st.session_state[test_key] = evaluate_test(
                model, manifest, blocks["Prueba"], blocks["Desarrollo"], manifest["settings"]["seed"]
            )
        if test_key in st.session_state:
            metrics, predictions = st.session_state[test_key]
            headline = st.columns(3)
            headline[0].metric("MAE del modelo", f"{metrics['MAE (pp)']:.3f} pp")
            headline[1].metric("MAE de persistencia", f"{metrics['MAE persistencia (pp)']:.3f} pp")
            headline[2].metric("Cobertura", f"{metrics['Cobertura (%)']:.1f} %")
            show_table("mae-externo", "Incluye la diferencia media por país y el intervalo bootstrap del 95 %. "
                       "Las unidades pp corresponden a puntos porcentuales.",
                       pd.Series(metrics, name="Valor"))
            selected = predictions[predictions.iso3 == country]
            if not selected.empty:
                show_chart("prueba-grafico", "La banda exploratoria se calibra únicamente en validación.",
                           forecast_chart(data[data.iso3 == country].tail(12), selected), width="stretch")
            residuals = predictions.assign(residuo=predictions.probability_pct - predictions["pronóstico"])
            chart = alt.Chart(residuals).mark_circle(color=BLUE, opacity=0.65).encode(
                x=alt.X("year:O", title="Año"), y=alt.Y("residuo:Q", title="Error (pp)"),
                tooltip=["iso3", "year", "residuo"],
            )
            show_chart("residuos", "El error se calcula como observado menos pronosticado.", chart, width="stretch")
            show_table("prueba-tabla", "Cada fila conserva la referencia de persistencia y el intervalo del modelo.",
                       predictions, hide_index=True)

    series = data[data.iso3 == country].set_index("year").probability_pct
    history = series.to_dict()
    eligible = sorted(year + 1 for year in history if year + 1 > manifest["cutoff"]
                      and all(year - lag in history for lag in range(3)))
    with motor:
        st.header("Motor de inferencia")
        st.caption(f"Modelo {manifest['model']} · artefacto {run}")
        if eligible:
            year = st.selectbox("Año objetivo", eligible, index=len(eligible) - 1)
            result, features = forecast(model, manifest, history, year)
            st.metric(f"{country_name(country)} · {year}", f"{result['pronóstico']:.2f} %")
            st.write(f"Persistencia {result['persistencia']:.2f} % · "
                     f"Banda exploratoria {result['inferior']:.2f}–{result['superior']:.2f} %")
            history_rows = series[series.index < year].tail(10).rename("probability_pct").reset_index()
            show_chart("pronostico", "Estimación poblacional a un año. El motor carga el artefacto sin reentrenar.",
                       forecast_chart(history_rows, pd.DataFrame([result])), width="stretch")
            st.code(f'python sp06_crisp/engine.py {run} {country} {year}', language="powershell")
        else:
            st.info("El país no tiene tres rezagos consecutivos para un año posterior al corte.")

    with explanation:
        st.header("Explicabilidad global y local")
        st.caption("Las atribuciones se expresan en la escala logarítmica del modelo. "
                   "Los rezagos correlacionados pueden compartir información.")
        shap_key = f"v2-shap-{run}"
        if st.button("Calcular SHAP"):
            st.session_state[shap_key] = shap_importance(model, blocks["Desarrollo"], FEATURES)
        if shap_key in st.session_state:
            show_bar("shap-global", "Importancia absoluta media calculada sobre el conjunto de desarrollo.",
                     st.session_state[shap_key], x="Rezago", y="SHAP medio absoluto", horizontal=True, color=BLUE)
            if eligible:
                background = blocks["Desarrollo"][FEATURES]
                values = shap_values(model, background, features)[0]
                log_value = float(model.predict(features)[0])
                base = log_value - float(values.sum())
                st.write(f"{country_name(country)} · {year} · valor base {base:.4f} · "
                         f"salida log {log_value:.4f} · probabilidad {result['pronóstico']:.2f} %")
                impacts = pd.DataFrame({"Rezago": FEATURES, "Aporte": values})
                chart = alt.Chart(impacts).mark_bar().encode(
                    x=alt.X("Aporte:Q", title="Aporte logarítmico"), y="Rezago:N",
                    color=alt.condition(alt.datum.Aporte >= 0, alt.value(BLUE), alt.value("#bd6b26")),
                    tooltip=["Rezago", "Aporte"],
                )
                show_chart("shap-local", "La suma del valor base y los aportes reproduce la salida del modelo.",
                           chart, width="stretch")

    with reports:
        st.header("Reportes y descargas")
        st.download_button("Descargar manifiesto", json.dumps(manifest, ensure_ascii=False, indent=2),
                           f"sp06-{run}.json", "application/json")
        if test_key not in st.session_state:
            st.info("Abre la prueba reservada para incluir sus métricas y predicciones en el informe.")
        else:
            metrics, predictions = st.session_state[test_key]
            kind = st.selectbox("Formato", ["PDF", "Word", "Excel"])
            key = (run, country, kind)
            selected = predictions[predictions.iso3 == country]
            if selected.empty:
                st.info("Selecciona un país con observaciones en la prueba reservada.")
            elif st.button("Preparar reporte"):
                chart = forecast_chart(data[data.iso3 == country].tail(12), selected)
                report_meta = {"fuente": manifest["source"]["source"], "modelo_ajustado": manifest["model"],
                               "hiperparámetros": manifest["params"], "dataset_sha256": manifest["dataset_sha256"],
                               "prueba_reservada": {"años": calendar["Prueba"]}}
                st.session_state.v2_report = (key, build_report(
                    kind, country_name(country), report_meta, metrics, tables["folds"], scores, predictions, chart
                ))
            saved = st.session_state.get("v2_report")
            if saved and saved[0] == key:
                payload, extension, mime = saved[1]
                st.download_button(f"Descargar {kind}", payload, f"sp06-{country}.{extension}", mime)

    with optimization:
        st.subheader("Historial de la corrida seleccionada")
        trials = tables["trials"]
        st.write(trials.estado.value_counts().to_dict())
        search = trials.assign(Búsqueda=trials.modelo + " · " + trials.fold.astype(str))
        show_line("optuna-avance", "El gráfico muestra el mejor MAE log acumulado por búsqueda.",
                  search, x="trial", y="mejor MAE log", color="Búsqueda", x_label="Trial")
        chart = alt.Chart(search).mark_boxplot(color=BLUE).encode(
            x=alt.X("MAE log:Q", title="MAE log por trial"), y=alt.Y("modelo:N", title="Modelo")
        )
        show_chart("optuna-distribucion", "La distribución reúne trials de distintas búsquedas del mismo modelo.",
                   chart, width="stretch")
        show_table("optuna-trials", "El historial identifica el estado, el error y la configuración de cada trial.",
                   trials, hide_index=True)
        final_trials = trials[(trials.fold == "Final") & (trials.estado == "COMPLETE")]
        if len(final_trials) >= 10:
            parameters = pd.DataFrame(final_trials["parámetros"].map(json.loads).tolist())
            importance = parameters.corrwith(final_trials["MAE log"].reset_index(drop=True),
                                             method="spearman").dropna().abs().rename("Asociación").reset_index()
            importance = importance.rename(columns={"index": "Parámetro"})
            if not importance.empty:
                show_bar("optuna-importancia", "Magnitud de Spearman en los trials finales. Es un diagnóstico "
                         "descriptivo de la búsqueda y depende de los rangos y combinaciones probadas.",
                         importance, x="Parámetro", y="Asociación", color=BLUE, horizontal=True)
