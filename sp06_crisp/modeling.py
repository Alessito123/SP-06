"""Nested country-group validation and a separate temporal holdout."""
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, shapiro, wilcoxon
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests
from xgboost import XGBRegressor

FEATURES = ["lag1", "lag2", "lag3"]
OUTER_START = 2015
HOLDOUT_START = 2018


def prepare(data):
    panel = data.sort_values(["iso3", "year"]).copy()
    by_country = panel.groupby("iso3")
    for lag, feature in enumerate(FEATURES, 1):
        panel[feature] = by_country.probability_pct.shift(lag).where(
            by_country.year.shift(lag).eq(panel.year - lag)
        )
    return panel.dropna(subset=FEATURES).assign(target=lambda rows: np.log1p(rows.probability_pct))


def candidates():
    return {
        "Ridge": (make_pipeline(StandardScaler(), Ridge()), {"ridge__alpha": [0.1, 1, 10]}),
        "Random Forest": (
            RandomForestRegressor(n_estimators=100, random_state=606, n_jobs=1),
            {"max_depth": [3, 6], "min_samples_leaf": [2, 5]},
        ),
        "XGBoost": (
            XGBRegressor(n_estimators=100, random_state=606, n_jobs=1),
            {"max_depth": [2, 3], "learning_rate": [0.03, 0.1]},
        ),
    }


def tune(name, rows):
    estimator, grid = candidates()[name]
    search = GridSearchCV(estimator, grid, cv=GroupKFold(5), scoring="neg_mean_absolute_error",
                          error_score="raise")
    return search.fit(rows[FEATURES], rows.target, groups=rows.iso3)


def validate(panel):
    development = panel[panel.year < HOLDOUT_START]
    folds, scores, errors = [], [], {}
    for number, (train, test) in enumerate(
        GroupKFold(5).split(development, groups=development.iso3), start=1
    ):
        earlier = development.iloc[train].query("year < @OUTER_START")
        later = development.iloc[test].query("year >= @OUTER_START")
        folds.append({"fold": number, "países de prueba": ", ".join(sorted(later.iso3.unique())),
                      "n entrenamiento": len(earlier), "n evaluación": len(later)})
        scores.append({"fold": number, "modelo": "Persistencia",
                       "MAE log": mean_absolute_error(later.target, np.log1p(later.lag1)),
                       "hiperparámetros": "—"})
        for name in candidates():
            search = tune(name, earlier)
            prediction = search.predict(later[FEATURES])
            absolute = abs(later.probability_pct.to_numpy() - np.expm1(prediction).clip(0, 100))
            errors.setdefault(name, []).extend(absolute)
            scores.append({"fold": number, "modelo": name,
                           "MAE log": mean_absolute_error(later.target, prediction),
                           "hiperparámetros": str(search.best_params_)})
    scores = pd.DataFrame(scores)
    ranking = scores.groupby("modelo")["MAE log"].mean().sort_values(kind="stable")
    winner = ranking.drop(index="Persistencia").index[0]
    radius = float(np.quantile(errors[winner], 0.90, method="higher"))
    return pd.DataFrame(folds), scores, ranking, winner, tune(winner, development), radius


def test_holdout(panel, search, radius):
    holdout = panel[panel.year >= HOLDOUT_START].copy()
    log_prediction = search.predict(holdout[FEATURES])
    holdout["pronóstico"] = np.expm1(log_prediction).clip(0, 100)
    holdout["persistencia"] = holdout.lag1
    holdout["inferior"] = (holdout["pronóstico"] - radius).clip(0, 100)
    holdout["superior"] = (holdout["pronóstico"] + radius).clip(0, 100)
    metrics = {
        "MAE log": mean_absolute_error(holdout.target, log_prediction),
        "MAE (pp)": mean_absolute_error(holdout.probability_pct, holdout["pronóstico"]),
        "RMSE (pp)": root_mean_squared_error(holdout.probability_pct, holdout["pronóstico"]),
        "MAE persistencia (pp)": mean_absolute_error(holdout.probability_pct, holdout.persistencia),
        "Cobertura (%)": 100 * holdout.probability_pct.between(holdout.inferior, holdout.superior).mean(),
    }
    return metrics, holdout[["iso3", "year", "probability_pct", "pronóstico", "persistencia", "inferior", "superior"]]


def statistical_tests(scores):
    wide = scores.pivot(index="fold", columns="modelo", values="MAE log")
    friedman = friedmanchisquare(*(wide[name] for name in wide))
    rows = []
    for left, right in combinations(wide.columns, 2):
        differences = wide[left] - wide[right]
        signed_rank = wilcoxon(differences).pvalue if differences.ne(0).any() else 1.0
        normality = shapiro(differences).pvalue if differences.nunique() > 1 else np.nan
        rows.append({"comparación": f"{left} / {right}", "Wilcoxon p": signed_rank,
                     "Shapiro–Wilk p": normality})
    pairs = pd.DataFrame(rows)
    pairs["Wilcoxon p Holm"] = multipletests(pairs["Wilcoxon p"], method="holm")[1]
    return friedman, pairs
