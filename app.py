import hashlib
import json
import os
from uuid import uuid4

import psycopg
import streamlit as st
from psycopg.types.json import Jsonb

from data import WDI_METADATA, WDI_URL, demo, public_dataset, read_panel, read_public_panel
from pipeline import METHODS, evaluate, metrics, paired, trends


def persist(result):
    run = uuid4()
    fingerprint, settings, predictions, scores, inference, _, _ = result
    clean = predictions.astype(object).where(predictions.notna(), None)
    fields = ["series", "origin", "horizon", "model", "observed", "forecast", "lower90", "upper90"]
    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5) as conn:
        conn.execute(
            "INSERT INTO p06_runs (run_id,input_sha256,settings,metrics) VALUES (%s,%s,%s,%s)",
            (run, fingerprint, Jsonb(settings),
             Jsonb({"scores": json.loads(scores.to_json(orient="records")), "inference": inference})),
        )
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO p06_predictions
                   (run_id,series,origin,horizon,model,observed,forecast,lower90,upper90)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                ((run, *row) for row in clean[fields].itertuples(index=False, name=None)),
            )
    return run


st.set_page_config(page_title="SP-06 Mortalidad prematura", layout="wide")
st.title("Pronóstico de mortalidad prematura por ENT")
st.caption("SP-06 · Flujo de investigación en siete fases")
data_tab, train_tab, motor_tab, validation_tab, interpretation_tab, web_tab, deploy_tab = st.tabs([
    "1. Datos", "2. Entrenamiento", "3. Motor", "4. Validación",
    "5. Interpretación", "6. Exploración web", "7. Despliegue",
])

with data_tab:
    st.header("Datos y procedencia")
    source = st.radio("Dataset para el entrenamiento", ["Público · OMS / Banco Mundial",
                                                       "Sintético · demostración", "CSV propio"])
    public = source.startswith("Público")
    synthetic = source.startswith("Sintético")
    unit = ("Probabilidad de morir entre los 30 y los 70 años (%) · ODS 3.4.1" if public
            else "Tasa estandarizada de 30 a 69 años por 100 000 habitantes")
    st.caption(unit)
    if public:
        content = public_dataset()
        public_panel = read_public_panel(content)
        with st.expander("Procedencia y cobertura del dataset público", expanded=True):
            st.markdown(f"**Fuente original** OMS, Global Health Observatory. "
                        f"**Publicación** [Banco Mundial, World Development Indicators]({WDI_URL}).")
            st.markdown(f"**Indicador** [SH.DYN.NCOM.ZS]({WDI_METADATA}) · CC BY 4.0. "
                        "Copia descargada el 9 de noviembre de 2026.")
            st.write(f"{public_panel.series.nunique()} países · {len(public_panel)} registros · "
                     f"{public_panel.year.min()}–{public_panel.year.max()}")
            st.caption("Estimaciones nacionales para ambos sexos y las cuatro causas combinadas. "
                       "El entrenamiento inicial usa el historial del indicador y la identidad de la serie.")
            country = st.selectbox("Serie histórica", sorted(public_panel.series.str.split("/").str[0].unique()))
            history_view = public_panel[public_panel.series == f"{country}/ambos/total"]
            st.line_chart(history_view, x="year", y="y", y_label="Probabilidad (%)")
            st.download_button("Descargar dataset público", content, "wdi_mortality.csv", "text/csv")
    elif synthetic:
        st.info("Datos generados por la aplicación para demostración.")
    else:
        st.info("Fuente proporcionada por el usuario. Cargue un panel armonizado por edad y causa.")

with train_tab:
    st.header("Entrenamiento")
    st.caption(f"Fuente seleccionada en fase 1 · {source}")
    with st.form("config"):
        raw = st.file_uploader("Panel agregado armonizado", type=["csv"]) if source == "CSV propio" else None
        origins = st.slider("Orígenes retrospectivos", 6, 25, 8)
        history = st.slider("Años mínimos consecutivos", 12, 20, 12)
        epochs = st.slider("Épocas de las redes", 5, 100, 30)
        available = ["Ingenuo", "ARIMA", "Ridge", "XGBoost", "LSTM_uni"] if public else METHODS
        chosen = st.multiselect("Modelos", available, default=["Ingenuo", "Ridge", "XGBoost"] if public else METHODS,
                                key=f"models_{public}")
        explain = st.checkbox("Calcular SHAP de XGBoost en el origen final")
        submit = st.form_submit_button("Entrenar modelos", type="primary")
    if submit:
        if not chosen or (source == "CSV propio" and raw is None):
            st.error("Seleccione modelos y una fuente.")
        else:
            if not public:
                content = demo() if synthetic else raw.getvalue()
            try:
                with st.spinner("Ajustando modelos por origen temporal"):
                    settings = dict(origins=origins, min_history=history, epochs=epochs,
                                    methods=chosen, explain=explain)
                    panel = public_panel if public else read_panel(content)
                    predictions, explanations = evaluate(panel, **settings, upper_limit=100 if public else float("inf"))
                    scores = metrics(predictions)
                    inference = paired(predictions)
                    st.session_state.pop("saved_run", None)
                    st.session_state.result = (hashlib.sha256(content).hexdigest(),
                                               {**settings, "synthetic": synthetic, "source": source,
                                                "indicator": "SH.DYN.NCOM.ZS" if public else "tasa_estandarizada",
                                                "source_url": WDI_URL if public else None, "unit": unit},
                                               predictions, scores, inference, explanations, trends(panel))
            except (ValueError, RuntimeError):
                st.error("No se completó el análisis. Revise el contrato del CSV y la longitud de las series.")



result = st.session_state.get("result")
if result is None:
    for tab in (motor_tab, validation_tab, interpretation_tab, web_tab, deploy_tab):
        tab.info("Entrena los modelos en la fase 2 para ver los resultados de esta sesión.")
else:
    fingerprint, settings, predictions, scores, inference, explanations, trend_table = result
    latest = predictions[predictions.origin == predictions.origin.max()]
    run_label = f"{settings.get('source', 'Corrida anterior')} · {settings.get('unit', '')}"

    with train_tab:
        st.success("Corrida disponible")
        st.caption(run_label)
        st.write("Modelos ejecutados", ", ".join(settings["methods"]))
        st.write("Último año de entrenamiento", int(latest.origin.max()))
        st.code(fingerprint, language=None)

    with motor_tab:
        st.header("Salida del motor de pronóstico")
        st.caption(run_label)
        st.info("Esta vista consulta los pronósticos calculados en fase 2. "
                "La inferencia independiente con modelos guardados sigue pendiente.")
        st.metric("Año de corte", int(latest.origin.max()))
        st.dataframe(latest.drop(columns=["scale"]), hide_index=True)

    with validation_tab:
        st.header("Validación temporal exploratoria")
        st.caption(run_label)
        st.dataframe(scores, hide_index=True)
        if inference:
            st.subheader("Comparación pareada de las LSTM")
            st.json(inference)

    with interpretation_tab:
        st.header("Explicabilidad y escenarios")
        st.caption(run_label)
        if explanations.empty:
            st.info("Selecciona XGBoost y activa SHAP en la fase 2 para generar atribuciones.")
        else:
            st.subheader("Atribuciones SHAP de XGBoost")
            st.dataframe(explanations, hide_index=True)
        total = latest[latest.series.str.endswith("/total")]
        if not total.empty:
            st.subheader("Escenarios de planificación")
            model = st.selectbox("Modelo de referencia", sorted(total.model.unique()))
            scenario = total[total.model == model][["series", "horizon", "forecast"]].copy()
            scenario["reduccion_adicional_2pct"] = scenario.forecast * 0.98 ** scenario.horizon
            scenario["aumento_adicional_2pct"] = scenario.forecast * 1.02 ** scenario.horizon
            if settings.get("indicator") == "SH.DYN.NCOM.ZS":
                scenario["aumento_adicional_2pct"] = scenario["aumento_adicional_2pct"].clip(upper=100)
            st.caption("Los escenarios aplican cambios anuales hipotéticos al valor pronosticado.")
            st.dataframe(scenario, hide_index=True)

    with web_tab:
        st.header("Explorar pronósticos")
        st.caption(run_label)
        series = st.selectbox("País / sexo / causa", sorted(latest.series.unique()))
        selection = latest[latest.series == series]
        model = st.selectbox("Modelo de pronóstico", sorted(selection.model.unique()))
        view = selection[selection.model == model].assign(
            year=lambda rows: rows.origin + rows.horizon
        )
        st.line_chart(view, x="year", y="forecast", x_label="Año", y_label=settings.get("unit"))
        st.dataframe(view[["year", "forecast", "lower90", "upper90"]], hide_index=True)
        if not trend_table.empty:
            with st.expander("Tendencias y quiebres exploratorios"):
                st.dataframe(trend_table, hide_index=True)
        st.download_button("Descargar pronósticos y validación", predictions.to_csv(index=False),
                           "p06-pronosticos.csv", "text/csv")

    with deploy_tab:
        st.header("Despliegue y trazabilidad")
        st.caption(run_label)
        if os.getenv("DATABASE_URL"):
            if st.button("Guardar ejecución en PostgreSQL", disabled="saved_run" in st.session_state):
                try:
                    st.session_state.saved_run = str(persist(result))
                    st.rerun()
                except psycopg.Error:
                    st.error("No se pudo guardar la ejecución. Revise la conexión y el esquema.")
            if "saved_run" in st.session_state:
                st.success(f"Ejecución guardada · {st.session_state.saved_run}")
        else:
            st.info("Configure DATABASE_URL para guardar la corrida en PostgreSQL.")
