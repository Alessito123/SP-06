import json
from pathlib import Path

import altair as alt
import pandas as pd

ISO_NUMERIC = dict(zip(
    "ARG BOL BRA CHL COL CRI CUB DOM ECU SLV GTM HTI HND MEX NIC PAN PRY PER URY VEN".split(),
    "032 068 076 152 170 188 192 214 218 222 320 332 340 484 558 591 600 604 858 862".split(),
))
BLUE = "#087e8b"


def country_map(rows, selected):
    topology = json.loads(Path(__file__).with_name("world-countries.json").read_text(encoding="utf-8"))
    countries = topology["objects"]["countries"]
    countries["geometries"] = [shape for shape in countries["geometries"]
                              if shape.get("id") in ISO_NUMERIC.values()]
    values = rows.assign(id=rows.iso3.map(ISO_NUMERIC))
    source = alt.InlineData(values=topology, format=alt.TopoDataFormat(type="topojson", feature="countries"))
    return (alt.Chart(source).mark_geoshape(stroke="white", strokeWidth=0.7)
            .transform_lookup(lookup="id", from_=alt.LookupData(values, "id", ["iso3", "probability_pct"]))
            .encode(stroke=alt.condition(alt.datum.iso3 == selected, alt.value("#102a43"), alt.value("white")),
                    strokeWidth=alt.condition(alt.datum.iso3 == selected, alt.value(2.8), alt.value(0.7)),
                    color=alt.Color("probability_pct:Q", title="Probabilidad (%)",
                                    scale=alt.Scale(scheme="tealblues")),
                    tooltip=[alt.Tooltip("properties.name:N", title="País"),
                             alt.Tooltip("probability_pct:Q", title="Probabilidad (%)", format=".1f")])
            .project(type="mercator").properties(height=440))


def correlation_chart(rows):
    matrix = rows.corr().rename_axis("variable").reset_index().melt(
        id_vars="variable", var_name="comparación", value_name="r"
    )
    base = alt.Chart(matrix).encode(x=alt.X("comparación:N", title=None),
                                    y=alt.Y("variable:N", title=None))
    cells = base.mark_rect().encode(color=alt.Color("r:Q", scale=alt.Scale(domain=[-1, 1],
                                                                          scheme="redblue")),
                                     tooltip=["variable", "comparación", alt.Tooltip("r:Q", format=".3f")])
    return (cells + base.mark_text(color="black", stroke="white", strokeWidth=0.4)
            .encode(text=alt.Text("r:Q", format=".2f"))).properties(height=220)


COUNTRY_NAMES = dict(zip(ISO_NUMERIC, (
    "Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Costa Rica", "Cuba",
    "República Dominicana", "Ecuador", "El Salvador", "Guatemala", "Haití", "Honduras",
    "México", "Nicaragua", "Panamá", "Paraguay", "Perú", "Uruguay", "Venezuela",
)))


def forecast_chart(history, predictions):
    base = alt.Chart(predictions).encode(x=alt.X("year:O", title="Año"))
    area = base.mark_area(color=BLUE, opacity=0.16).encode(
        y=alt.Y("inferior:Q", title="Probabilidad (%)", scale=alt.Scale(zero=False)),
        y2="superior:Q",
    )
    if len(predictions) == 1:
        area = base.mark_rule(color=BLUE, strokeWidth=5, opacity=0.4).encode(
            y=alt.Y("inferior:Q", title="Probabilidad (%)", scale=alt.Scale(zero=False)),
            y2="superior:Q",
        )
    predicted = predictions.melt(id_vars="year", value_vars=["pronóstico", "persistencia"],
                                 var_name="Serie", value_name="Valor")
    observed = history.rename(columns={"probability_pct": "Valor"}).assign(Serie="observado")
    lines = alt.Chart(pd.concat([observed, predicted], ignore_index=True)).mark_line(point=True).encode(
        x=alt.X("year:O", title="Año"),
        y=alt.Y("Valor:Q", title="Probabilidad (%)", scale=alt.Scale(zero=False)),
        color=alt.Color("Serie:N", scale=alt.Scale(
            domain=["observado", "pronóstico", "persistencia"], range=["#23395d", BLUE, "#bd6b26"]
        )),
        tooltip=["year", "Serie", alt.Tooltip("Valor:Q", format=".2f")],
    )
    return (area + lines).properties(height=330)


def shap_values(search, background, inputs):
    import shap

    fitted = search.best_estimator_
    if hasattr(fitted, "steps"):
        transform = fitted[:-1]
        explanation = shap.LinearExplainer(fitted.steps[-1][1], transform.transform(background))
        return explanation(transform.transform(inputs)).values
    return shap.TreeExplainer(fitted)(inputs).values


def shap_importance(search, rows, features):
    inputs = rows[features]
    values = shap_values(search, inputs, inputs)
    return pd.DataFrame({"Rezago": features, "SHAP medio absoluto": abs(values).mean(axis=0)})
