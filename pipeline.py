from collections import defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from xgboost import XGBRegressor

from data import COV

H = 5
WINDOW = 6
METHODS = ["Ingenuo", "ARIMA", "Ridge", "XGBoost", "LSTM_uni", "LSTM", "TFT", "Hibrido"]


def slope(sequence):
    t = np.arange(WINDOW) - (WINDOW - 1) / 2
    return sequence @ t / (t @ t)


def tabular(x, group, groups):
    return np.column_stack([x.reshape(len(x), -1), np.eye(groups)[group]])


def evaluate(panel, origins=8, min_history=12, epochs=30, methods=METHODS, explain=False,
             upper_limit=np.inf):
    """Reajusta cada origen. La última fecha común se usa para pronóstico."""
    series = {key: frame.set_index("year").sort_index() for key, frame in panel.groupby("series")}
    first = int(panel.year.min())
    last = int(panel.year.max())
    residuals = defaultdict(list)
    records = []
    explanations = []
    for origin in range(max(first + min_history - 1, last - origins), last + 1):
        train_x, train_y, train_group = [], [], []
        test_x, test_group, metadata = [], [], []
        for key, frame in series.items():
            if origin not in frame.index:
                continue
            start = origin
            while start - 1 in frame.index:
                start -= 1
            if origin - start + 1 < min_history:
                continue
            observed = frame.loc[start:origin, "y"].to_numpy()
            group = len(metadata)
            for base in range(start + WINDOW - 1, origin):
                years = np.arange(base + 1, base + 1 + H)
                target = frame.y.reindex(years).where(years <= origin).to_numpy()
                train_x.append(window(frame, base))
                train_y.append(target)
                train_group.append(group)
            test_x.append(window(frame, origin))
            test_group.append(group)
            metadata.append((key, frame, observed))
        if not metadata:
            continue
        x, y, group = map(np.array, (train_x, train_y, train_group))
        test, tg = np.array(test_x), np.array(test_group)
        forecasts = {}
        if "Ingenuo" in methods:
            forecasts["Ingenuo"] = np.repeat(test[:, -1, :1], H, axis=1)
        if "ARIMA" in methods:
            forecasts["ARIMA"] = np.array([
                ARIMA(history, order=(1, 1, 0)).fit().forecast(H) for _, _, history in metadata
            ])
        for method in set(methods) & {"Ridge", "XGBoost"}:
            train_tab = tabular(x, group, len(tg))
            test_tab = tabular(test, tg, len(tg))
            predictions = []
            for h in range(H):
                valid = np.isfinite(y[:, h])
                if method == "Ridge":
                    model = make_pipeline(SimpleImputer(keep_empty_features=True), StandardScaler(), Ridge(alpha=10))
                else:
                    model = XGBRegressor(n_estimators=120, max_depth=2, learning_rate=0.05,
                                         n_jobs=1, random_state=606, objective="reg:squarederror")
                model.fit(train_tab[valid], y[valid, h])
                predictions.append(model.predict(test_tab))
                if explain and method == "XGBoost" and origin == last:
                    import shap
                    scores = np.abs(shap.TreeExplainer(model)(test_tab).values).mean(axis=0)
                    for j, name in enumerate(["y", *COV]):
                        explanations.append({"horizon": h + 1, "feature": name, "mean_abs_sum": scores[j:WINDOW * 4:4].sum()})
                    explanations.append({"horizon": h + 1, "feature": "serie", "mean_abs_sum": scores[WINDOW * 4:].sum()})
            forecasts[method] = np.array(predictions).T
        for method in set(methods) & {"LSTM", "LSTM_uni", "TFT", "Hibrido"}:
            from models import neural

            if method == "Hibrido":
                steps = np.arange(1, H + 1)
                trend = x[:, -1, :1] + slope(x[:, :, 0])[:, None] * steps
                future_trend = test[:, -1, :1] + slope(test[:, :, 0])[:, None] * steps
                forecasts[method] = future_trend + neural(x, y - trend, group, test, tg, "LSTM", epochs)
            else:
                width = 1 if method == "LSTM_uni" else x.shape[2]
                forecasts[method] = neural(x[:, :, :width], y, group, test[:, :, :width], tg, method, epochs)
        for method, prediction in forecasts.items():
            for i, (key, frame, history) in enumerate(metadata):
                scale = np.abs(np.diff(history)).mean()
                for h, value in enumerate(prediction[i], 1):
                    value = max(float(value), 0)
                    if not np.isfinite(value):
                        raise RuntimeError("El modelo produjo un pronóstico no finito.")
                    value = min(value, upper_limit)
                    actual = frame.y.get(origin + h, np.nan)
                    pool = residuals[method, h, key.split("/")[-1]]
                    matured = sorted(error for year, error in pool if year <= origin)
                    rank = int(np.ceil((len(matured) + 1) * 0.9))
                    radius = matured[rank - 1] if rank <= len(matured) else np.nan
                    records.append(dict(series=key, origin=origin, horizon=h, model=method,
                                        observed=actual, forecast=value, lower90=max(value - radius, 0),
                                        upper90=min(value + radius, upper_limit), scale=scale))
                    if np.isfinite(actual):
                        pool.append((origin + h, abs(actual - value)))
    if not records:
        raise ValueError("Se requieren series con suficientes años consecutivos.")
    return pd.DataFrame(records), pd.DataFrame(explanations)


def window(frame, origin):
    years = np.arange(origin - WINDOW + 1, origin + 1)
    y = frame.y.reindex(years).to_numpy()
    cov = frame[COV].reindex(years - 1).to_numpy()
    return np.column_stack([y, cov])


def trends(panel):
    """Tendencias descriptivas del tramo consecutivo más reciente."""
    results = []
    for key, frame in panel.groupby("series"):
        frame = frame.sort_values("year")
        splits = np.flatnonzero(np.diff(frame.year) != 1) + 1
        frame = frame.iloc[splits[-1] if len(splits) else 0:]
        if len(frame) < 10 or (frame.y <= 0).any():
            continue
        years = frame.year.to_numpy()
        t = years - years[0]
        y = np.log(frame.y.to_numpy())
        best = None
        for count in range(3):
            for knots in combinations(range(5, len(y) - 4), count):
                edges = (0, *knots, len(y))
                if min(np.diff(edges)) < 5:
                    continue
                design = np.column_stack([np.ones(len(y)), t, *[np.maximum(t - k, 0) for k in knots]])
                coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
                mse = max(np.mean((y - design @ coefficients) ** 2), 1e-15)
                bic = len(y) * np.log(mse) + (2 + 2 * count) * np.log(len(y))
                if best is None or bic < best[0]:
                    best = (bic, knots, coefficients)
        _, knots, coefficients = best
        results.append({"series": key, "start": int(years[0]), "end": int(years[-1]),
                        "breaks": ", ".join(str(years[k]) for k in knots),
                        "latest_annual_change_pct": 100 * np.expm1(coefficients[1:].sum())})
    return pd.DataFrame(results)


def metrics(predictions):
    valid = predictions.dropna(subset=["observed"]).copy()
    error = valid.observed - valid.forecast
    valid["MAE"] = error.abs()
    valid["RMSE"] = error ** 2
    valid["MASE"] = error.abs() / valid.scale.where(valid.scale > 0)
    valid["coverage90"] = ((valid.observed >= valid.lower90) & (valid.observed <= valid.upper90)).where(valid.lower90.notna())
    valid["width90"] = valid.upper90 - valid.lower90
    valid["cause"] = valid.series.str.split("/").str[-1]
    summary = valid.groupby(["model", "cause", "horizon"]).agg(
        n=("MAE", "size"), n_mase=("MASE", "count"), n_intervals=("coverage90", "count"),
        MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), MASE=("MASE", "mean"),
        coverage90=("coverage90", "mean"), width90=("width90", "mean"),
    ).reset_index()
    summary["RMSE"] = np.sqrt(summary.RMSE)
    return summary


def paired(predictions, reps=2000, block=3):
    """Remuestrea orígenes consecutivos manteniendo juntos países y sexos."""
    subset = predictions[(predictions.horizon == 1) & predictions.series.str.endswith("/total")].dropna(subset=["observed"])
    subset = subset[subset.scale > 0].copy()
    subset["loss"] = (subset.forecast - subset.observed).abs() / subset.scale
    table = subset.pivot(index=["origin", "series"], columns="model", values="loss")
    if not {"LSTM", "LSTM_uni"}.issubset(table.columns):
        return {}
    table = table[["LSTM", "LSTM_uni"]].dropna()
    table["country"] = table.index.get_level_values("series").str[:3]
    values = table.groupby(["origin", "country"])[["LSTM", "LSTM_uni"]].mean().groupby("origin").mean()
    if len(values) < max(6, 2 * block) or not np.all(np.diff(values.index) == 1):
        return {"origins": len(values), "status": "Orígenes consecutivos insuficientes"}
    array = values.to_numpy()
    rng = np.random.default_rng(606)
    starts = rng.integers(0, len(array) - block + 1, size=(reps, int(np.ceil(len(array) / block))))
    samples = array[(starts[..., None] + np.arange(block)).reshape(reps, -1)[:, :len(array)]]
    delta = array[:, 0] - array[:, 1]
    boot = samples[:, :, 0] - samples[:, :, 1]
    instability = samples[:, :, 0].std(axis=1, ddof=1) - samples[:, :, 1].std(axis=1, ddof=1)
    return {"origins": len(array), "delta_mase": float(delta.mean()),
            "ci95_delta": np.quantile(boot.mean(axis=1), [0.025, 0.975]).tolist(),
            "delta_sd": float(array[:, 0].std(ddof=1) - array[:, 1].std(ddof=1)),
            "ci95_sd": np.quantile(instability, [0.025, 0.975]).tolist()}
