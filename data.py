"""Contrato de entrada agregado, de cobertura nacional."""
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd

AGES = list(range(30, 70, 5))
WEIGHTS = np.array([7.61, 7.15, 6.59, 6.04, 5.37, 4.55, 3.72, 2.96])
WEIGHTS /= WEIGHTS.sum()
CAUSES = ["cvd", "cancer", "diabetes", "resp"]
KEY = ["iso3", "sex", "year", "age"]
COLS = KEY + ["population", "coverage", *CAUSES, "gdp", "urban"]
COV = ["log_gdp", "urban", "share60"]

WDI_URL = "https://data.worldbank.org/indicator/SH.DYN.NCOM.ZS"
WDI_METADATA = "https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SH.DYN.NCOM.ZS"


def public_dataset():
    return Path(__file__).with_name("wdi_mortality.csv").read_bytes()


def read_public_panel(raw):
    frame = pd.read_csv(io.BytesIO(raw))
    if (not frame.iso3.str.fullmatch(r"[A-Z]{3}", na=False).all()
        or frame.duplicated(["iso3", "year"]).any()
        or not frame.probability_pct.between(0, 100).all()):
        raise ValueError("El panel público contiene observaciones inválidas.")
    return frame.assign(series=frame.iso3 + "/ambos/total", y=frame.probability_pct,
                        **dict.fromkeys(COV, np.nan))[["series", "year", "y", *COV]]


def read_panel(raw, min_coverage=0.85):
    if len(raw) > 20_000_000:
        raise ValueError("El archivo supera 20 MB.")
    frame = pd.read_csv(io.BytesIO(raw), dtype={"iso3": str, "sex": str})
    if set(frame.columns) != set(COLS) or frame.empty or len(frame) > 100_000:
        raise ValueError("Columnas o tamaño incompatibles con el contrato.")
    if not frame.iso3.fillna("").map(lambda s: bool(re.fullmatch("[A-Z]{3}", s))).all():
        raise ValueError("ISO3 inválido.")
    if not frame.sex.isin(["F", "M"]).all() or frame.duplicated(KEY).any():
        raise ValueError("Sexo inválido o clave duplicada.")
    numeric = [c for c in COLS if c not in ["iso3", "sex"]]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="raise")
    if np.isinf(frame[numeric].to_numpy()).any():
        raise ValueError("Se encontraron infinitos.")
    required = ["year", "age", "population", "coverage", *CAUSES]
    if frame[required].isna().any().any():
        raise ValueError("Faltan datos obligatorios. Omita el estrato incompleto.")
    if (
        not frame.age.isin(AGES).all()
        or not frame.year.between(1950, 2100).all()
        or (frame.year % 1 != 0).any()
        or (frame.population <= 0).any()
        or not frame.coverage.between(0, 1).all()
        or (frame[CAUSES] < 0).any().any()
        or (frame[CAUSES] % 1 != 0).any().any()
        or (frame[CAUSES].sum(axis=1) > frame.population).any()
        or (frame.gdp.dropna() <= 0).any()
        or not frame.urban.dropna().between(0, 100).all()
    ):
        raise ValueError("Valores fuera de rango.")
    output = []
    for (country, sex, year), rows in frame.groupby(KEY[:3]):
        if len(rows) != 8 or rows.coverage.min() < min_coverage:
            continue
        for name in ["gdp", "urban"]:
            if rows[name].nunique(dropna=False) != 1:
                raise ValueError("Covariable incompatible entre grupos de edad.")
        rows = rows.sort_values("age")
        rates = rows[CAUSES].to_numpy() / rows.population.to_numpy()[:, None]
        targets = dict(zip(CAUSES, 100_000 * WEIGHTS @ rates))
        targets["total"] = sum(targets.values())
        cov = {
            "log_gdp": np.log(rows.gdp.iloc[0]),
            "urban": rows.urban.iloc[0],
            "share60": rows.population.iloc[-2:].sum() / rows.population.sum(),
        }
        for cause, y in targets.items():
            output.append({"series": f"{country}/{sex}/{cause}", "year": int(year), "y": y, **cov})
    if not output:
        raise ValueError("No hay estratos completos con cobertura suficiente.")
    return pd.DataFrame(output)


def demo():
    rng = np.random.default_rng(606)
    rows = []
    for i, country in enumerate(["PER", "CHL", "COL", "MEX"]):
        for sex in ["F", "M"]:
            for year in range(2000, 2025):
                gdp = 6500 * np.exp(0.026 * (year - 2000)) + i * 1500
                for age in AGES:
                    pop = 130_000 + 900 * (year - 2000) - 1400 * (age - 30)
                    rate = 70 * np.exp(0.065 * (age - 30) - 0.014 * (year - 2000))
                    rate *= (1 + 0.12 * i + 0.21 * (sex == "M")) * (1 + 0.15 * (year in [2020, 2021]))
                    deaths = rng.poisson(pop / 100_000 * rate * np.array([0.48, 0.32, 0.12, 0.08]))
                    rows.append([country, sex, year, age, pop, 0.97, *deaths, gdp, 65 + 0.4 * (year - 2000)])
    return pd.DataFrame(rows, columns=COLS).to_csv(index=False).encode()
