"""Panel validation, chronological partitioning and nested Optuna search."""
import json
from io import BytesIO

import numpy as np
import optuna
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from modeling import FEATURES, prepare

SPACES = {
    "Ridge": {"alpha": (0.001, 100.0, "log")},
    "Random Forest": {
        "n_estimators": (100, 400, "int"), "max_depth": (2, 8, "int"),
        "min_samples_leaf": (2, 10, "int"),
    },
    "XGBoost": {
        "n_estimators": (50, 300, "int"), "max_depth": (2, 4, "int"),
        "learning_rate": (0.01, 0.15, "log"), "subsample": (0.7, 1.0, "float"),
    },
}


def read_data(content):
    if len(content) > 2_000_000:
        raise ValueError("El CSV supera 2 MB.")
    frame = pd.read_csv(BytesIO(content), dtype={"iso3": "string"})
    required = ["iso3", "year", "probability_pct"]
    if set(frame.columns) != set(required) or frame.empty:
        raise ValueError("El CSV debe contener iso3, year y probability_pct.")
    if not frame.iso3.str.fullmatch(r"[A-Z]{3}", na=False).all():
        raise ValueError("Usa códigos de país de tres letras mayúsculas.")
    years = pd.to_numeric(frame.year, errors="coerce")
    values = pd.to_numeric(frame.probability_pct, errors="coerce")
    if not (years.between(1900, 2100) & years.mod(1).eq(0)).all():
        raise ValueError("Los años deben ser enteros entre 1900 y 2100.")
    if not values.between(0, 100).all():
        raise ValueError("Cada probabilidad debe estar entre 0 y 100 y tener un valor.")
    frame = frame.assign(year=years.astype(int), probability_pct=values)
    if frame.duplicated(["iso3", "year"]).any():
        raise ValueError("Hay claves país-año duplicadas.")
    return frame.sort_values(["iso3", "year"]).reset_index(drop=True)


def split_panel(frame):
    years = sorted(int(year) for year in frame.year.unique())
    if len(years) < 14:
        raise ValueError("Se requieren al menos 14 años para el protocolo anidado.")
    quotas = np.array([0.70, 0.15, 0.15]) * len(years)
    sizes = quotas.astype(int)
    for index in np.argsort(-(quotas - sizes), kind="stable")[:len(years) - sizes.sum()]:
        sizes[index] += 1
    development_end, validation_end = np.cumsum(sizes)[:2]
    calendar = {
        "Desarrollo": years[:development_end],
        "Validación": years[development_end:validation_end],
        "Prueba": years[validation_end:],
    }
    panel = prepare(frame)
    blocks = {name: panel[panel.year.isin(period)] for name, period in calendar.items()}
    if any(block.empty for block in blocks.values()):
        raise ValueError("Los bloques necesitan observaciones con tres rezagos consecutivos.")
    return calendar, blocks


def estimator(name, params, seed):
    if name == "Ridge":
        return make_pipeline(StandardScaler(), Ridge(**params))
    if name == "Random Forest":
        return RandomForestRegressor(**params, random_state=seed, n_jobs=1)
    return XGBRegressor(**params, random_state=seed, n_jobs=1, objective="reg:squarederror")


def evaluate_nested(development, settings, progress):
    """Only development rows enter model selection and hyperparameter search."""
    names = settings["models"]
    seed = settings["seed"]
    fold_scores, fold_details, history = [], [], []
    years = sorted(development.year.unique())
    cutoff = years[-max(2, len(years) // 4)]
    if development.iso3.nunique() < 5:
        raise ValueError("Se requieren al menos cinco países con rezagos válidos.")
    partitions = []
    for train, test in GroupKFold(5).split(development, groups=development.iso3):
        earlier = development.iloc[train].query("year < @cutoff")
        later = development.iloc[test].query("year >= @cutoff")
        if earlier.iso3.nunique() < 3 or later.empty:
            raise ValueError("La cobertura impide formar cinco folds externos y tres internos.")
        partitions.append((earlier, later))
    total = (5 * len(names) + 1) * settings["trials"]

    def tune(name, rows, fold):
        splits = list(GroupKFold(3).split(rows, groups=rows.iso3))

        def objective(trial):
            params = {}
            for key, (low, high, kind) in settings["spaces"][name].items():
                params[key] = (trial.suggest_int(key, low, high) if kind == "int"
                               else trial.suggest_float(key, low, high, log=kind == "log"))
            errors = []
            for step, (train, test) in enumerate(splits):
                fitted = estimator(name, params, seed).fit(rows.iloc[train][FEATURES], rows.iloc[train].target)
                errors.append(mean_absolute_error(rows.iloc[test].target, fitted.predict(rows.iloc[test][FEATURES])))
                trial.report(float(np.mean(errors)), step)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            return float(np.mean(errors))

        def record(study, trial):
            completed = [t.value for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
            history.append({"fold": fold, "modelo": name, "trial": trial.number + 1,
                            "estado": trial.state.name, "MAE log": trial.value,
                            "mejor MAE log": min(completed, default=None),
                            "parámetros": json.dumps(trial.params)})
            progress(len(history), total, history[-1])

        study = optuna.create_study(
            sampler=optuna.samplers.TPESampler(seed=seed), direction="minimize",
            pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=1),
        )
        study.optimize(objective, n_trials=settings["trials"], timeout=settings["timeout"],
                       callbacks=[record], catch=(ValueError,))
        if not any(trial.state == optuna.trial.TrialState.COMPLETE for trial in study.trials):
            raise ValueError(f"Optuna no completó trials válidos para {name} en el fold {fold}.")
        return study.best_params

    for fold, (earlier, later) in enumerate(partitions, 1):
        fold_details.append({"fold": fold, "países de prueba": ", ".join(sorted(later.iso3.unique())),
                             "países de ajuste": ", ".join(sorted(earlier.iso3.unique())),
                             "años de ajuste": f"{earlier.year.min()}–{earlier.year.max()}",
                             "años de evaluación": f"{later.year.min()}–{later.year.max()}",
                             "n entrenamiento": len(earlier), "n evaluación": len(later)})
        fold_scores.append({"fold": fold, "modelo": "Persistencia",
                            "MAE log": mean_absolute_error(later.target, np.log1p(later.lag1)),
                            "hiperparámetros": "—"})
        for name in names:
            params = tune(name, earlier, str(fold))
            fitted = estimator(name, params, seed).fit(earlier[FEATURES], earlier.target)
            fold_scores.append({"fold": fold, "modelo": name,
                                "MAE log": mean_absolute_error(later.target, fitted.predict(later[FEATURES])),
                                "hiperparámetros": str(params)})
    scores = pd.DataFrame(fold_scores)
    ranking = scores.groupby("modelo")["MAE log"].mean()
    winner = ranking.drop("Persistencia").idxmin()
    params = tune(winner, development, "Final")
    fitted = estimator(winner, params, seed).fit(development[FEATURES], development.target)
    return fitted, winner, params, pd.DataFrame(fold_details), scores, pd.DataFrame(history)


def calibrate(model, validation):
    error = abs(validation.probability_pct - np.expm1(model.predict(validation[FEATURES])).clip(0, 100))
    return float(np.quantile(error, 0.90, method="higher"))
