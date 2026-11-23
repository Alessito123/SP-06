"""Frozen exploratory rolling-origin experiments. Invoke with python research.py."""
import argparse
import hashlib
import json
import subprocess
import time
import warnings
from pathlib import Path
from importlib.metadata import version

import numpy as np
import optuna
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from xgboost import XGBRegressor

from protocol_v2 import read_data

BASELINES = ["Persistencia", "Deriva amortiguada", "Media móvil", "ETS", "ARIMA"]
LEARNERS = ["Ridge", "Elastic Net", "Random Forest", "XGBoost", "HistGradientBoosting"]
ROOT = Path(__file__).parent
CONFIG = ROOT / "science/protocol.json"


def features(data, mode):
    result = data.sort_values(["iso3", "year"]).copy()
    group = result.groupby("iso3")
    columns = []
    for lag in range(1, 6):
        name = f"lag{lag}"
        result[name] = group.probability_pct.shift(lag).where(group.year.shift(lag).eq(result.year - lag))
        columns.append(name)
    # A common five-year history preserves identical evaluation cells across ablations.
    result = result.dropna(subset=columns).copy()
    result["delta"] = result.probability_pct - result.lag1
    if mode == "lag3":
        return result, columns[:3]
    if mode == "lag5":
        return result, columns
    lagged = result[columns].to_numpy()
    result["difference"] = lagged[:, 0] - lagged[:, 1]
    result["relative"] = np.divide(result.difference, result.lag2,
                                  out=np.zeros(len(result)), where=result.lag2.to_numpy() != 0)
    result["mean"] = lagged.mean(axis=1)
    result["volatility"] = lagged.std(axis=1)
    result["slope"] = (lagged[:, ::-1] @ np.arange(-2, 3)) / 10
    result["trend_distance"] = result.lag1 - (result["mean"] + 2 * result.slope)
    return result, columns + ["difference", "relative", "mean", "volatility", "slope", "trend_distance"]


def learner(name, trial, seed):
    if name in ("Ridge", "Elastic Net"):
        alpha = trial.suggest_float("alpha", .001, 100, log=True)
        estimator = Ridge(alpha=alpha) if name == "Ridge" else ElasticNet(
            alpha=alpha, l1_ratio=trial.suggest_float("l1_ratio", .05, .95), max_iter=10000)
        return make_pipeline(StandardScaler(), estimator)
    if name == "Random Forest":
        return RandomForestRegressor(n_estimators=trial.suggest_int("n_estimators", 100, 200),
                                     max_depth=trial.suggest_int("max_depth", 2, 6),
                                     min_samples_leaf=trial.suggest_int("min_samples_leaf", 2, 10),
                                     random_state=seed, n_jobs=1)
    if name == "HistGradientBoosting":
        return HistGradientBoostingRegressor(max_iter=trial.suggest_int("max_iter", 50, 150),
                                            max_leaf_nodes=trial.suggest_int("max_leaf_nodes", 3, 12),
                                            learning_rate=trial.suggest_float("learning_rate", .01, .15, log=True),
                                            random_state=seed)
    if name == "CatBoost":
        from catboost import CatBoostRegressor
        return CatBoostRegressor(iterations=trial.suggest_int("iterations", 50, 150),
                                 depth=trial.suggest_int("depth", 2, 4),
                                 learning_rate=trial.suggest_float("learning_rate", .01, .15, log=True),
                                 random_seed=seed, verbose=False, thread_count=1)
    return XGBRegressor(n_estimators=trial.suggest_int("n_estimators", 50, 150),
                        max_depth=trial.suggest_int("max_depth", 2, 4),
                        learning_rate=trial.suggest_float("learning_rate", .01, .15, log=True),
                        subsample=trial.suggest_float("subsample", .7, 1), random_state=seed, n_jobs=1)


def predict_model(model, rows, columns, target):
    values = model.predict(rows[columns])
    return np.clip(rows.lag1.to_numpy() + values if target == "difference" else np.expm1(values), 0, 100)


def baseline(data, country, year, name):
    history = data[(data.iso3 == country) & (data.year < year)].sort_values("year").probability_pct.to_numpy()
    if name == "Persistencia":
        value = history[-1]
    elif name == "Deriva amortiguada":
        value = history[-1] + .5 * np.diff(history[-4:]).mean()
    elif name == "Media móvil":
        value = history[-3:].mean()
    elif name == "ETS":
        value = ExponentialSmoothing(history, trend="add", damped_trend=True,
                                     initialization_method="estimated").fit().forecast(1)[0]
    else:
        value = ARIMA(history, order=(1, 1, 0)).fit().forecast(1)[0]
    return float(np.clip(value, 0, 100))


def quantile(errors, alpha, corrected):
    errors = np.sort(np.asarray(errors))
    rank = int(np.ceil((len(errors) + 1) * (1 - alpha))) if corrected else int(np.ceil(len(errors) * (1-alpha)))
    return float(errors[min(rank, len(errors)) - 1])


def run(output, models, budgets, modes):
    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes.decode("utf-8-sig"))
    data_path = ROOT / "wdi_mortality.csv"
    raw = data_path.read_bytes()
    data = read_data(raw)
    records, trials_log, events = [], [], []
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    output.mkdir(parents=True, exist_ok=False)
    for mode in modes:
        rows, columns = features(data, mode)
        for name in models:
            targets = ["level", "difference"] if name not in BASELINES else ["level"]
            for target in targets:
                for budget in ([0] if name in BASELINES else budgets):
                    experiment = f"{name}-{mode}-{target}-{budget}"
                    for year in config["outer_years"]:
                        start = time.monotonic()
                        earlier = rows[rows.year < year]
                        later = rows[rows.year == year]
                        if name in BASELINES:
                            predictions = [baseline(data, country, year, name) for country in later.iso3]
                            params = {}
                        else:
                            def objective(trial):
                                errors = []
                                for inner_year in range(year - 3, year):
                                    train = earlier[earlier.year < inner_year]
                                    validation = earlier[earlier.year == inner_year]
                                    model = learner(name, trial, config["seed"])
                                    truth = train.delta if target == "difference" else np.log1p(train.probability_pct)
                                    model.fit(train[columns], truth)
                                    prediction = predict_model(model, validation, columns, target)
                                    errors.append(float(np.abs(validation.probability_pct - prediction).mean()))
                                # No pruning: three dependent temporal blocks are too few for stable pruning.
                                return float(np.mean(errors))

                            study = optuna.create_study(direction="minimize",
                                sampler=optuna.samplers.TPESampler(seed=config["seed"], n_startup_trials=10),
                                pruner=optuna.pruners.NopPruner())
                            def log_trial(study, trial):
                                entry = {"experiment": experiment, "year": year, "trial": trial.number,
                                         "value": trial.value, "state": trial.state.name, "params": trial.params,
                                         "duration": trial.duration.total_seconds() if trial.duration else None}
                                trials_log.append(entry)
                                with (output / "trials.jsonl").open("a", encoding="utf8") as stream:
                                    stream.write(json.dumps(entry) + "\n")
                            study.optimize(objective, n_trials=budget, callbacks=[log_trial])
                            params = study.best_params
                            model = learner(name, optuna.trial.FixedTrial(params), config["seed"])
                            truth = earlier.delta if target == "difference" else np.log1p(earlier.probability_pct)
                            model.fit(earlier[columns], truth)
                            predictions = predict_model(model, later, columns, target)
                        duration = time.monotonic() - start
                        for (_, row), prediction in zip(later.iterrows(), predictions):
                            past = data[(data.iso3 == row.iso3) & (data.year < year)].sort_values("year")
                            scale = past.probability_pct.diff().abs().mean()
                            records.append({"experiment": experiment, "model": name, "features": mode,
                                            "target": target, "budget": budget, "year": year, "iso3": row.iso3,
                                            "observed": row.probability_pct, "forecast": prediction,
                                            "baseline": row.lag1, "scale": scale, "params": json.dumps(params),
                                            "train_start": int(earlier.year.min()), "train_end": year-1,
                                            "duration": duration})
                        pd.DataFrame(records).to_csv(output / "predictions.csv", index=False)
                        print(experiment, year, flush=True)
    predictions = pd.DataFrame(records)
    summaries, intervals = [], []
    for experiment, group in predictions.groupby("experiment"):
        error = abs(group.observed-group.forecast)
        naive = abs(group.observed-group.baseline)
        country = (error-naive).groupby(group.iso3).mean()
        rng = np.random.default_rng(config["seed"])
        ci = np.quantile(rng.choice(country.to_numpy(), (5000,len(country))).mean(axis=1), [.025,.975])
        first = group.iloc[0]
        summaries.append({"experiment": experiment, "model": first.model, "features": first.features,
                          "target": first.target, "budget": first.budget, "MAE": error.mean(),
                          "RMSE": np.sqrt(np.mean((group.observed-group.forecast)**2)),
                          "MASE": (error/group.scale.replace(0,np.nan)).mean(), "delta_MAE": country.mean(),
                          "CI_lower": ci[0], "CI_upper": ci[1], "countries_better_pct": 100*country.lt(0).mean(),
                          "train_start": group.train_start.min(), "last_train_year": group.train_end.max(),
                          "validation_start": group.year.min(), "validation_end": group.year.max(),
                          "seconds": group.groupby("year").duration.first().sum(), "seed": config["seed"]})
        for year in sorted(group.year.unique())[2:]:
            past = group[group.year < year]
            test = group[group.year == year]
            residuals = abs(past.observed-past.forecast)
            for method in ["empirical", "pooled_conformal", "year_block_conformal"]:
                values = (residuals.groupby(past.year).max() if method == "year_block_conformal" else residuals)
                radius = quantile(values, .1, method != "empirical")
                lo = (test.forecast-radius).clip(0,100)
                hi = (test.forecast+radius).clip(0,100)
                for idx, row in test.iterrows():
                    intervals.append({"experiment":experiment,"method":method,"year":year,"iso3":row.iso3,
                                      "coverage":lo[idx]<=row.observed<=hi[idx],"width":hi[idx]-lo[idx],
                                      "nominal":.9,"calibration_last_year":year-1,"calibration_n":len(values),
                                      "finite_rank_capped":int(np.ceil((len(values)+1)*.9))>len(values)})
    summary = pd.DataFrame(summaries).sort_values("MAE")
    summary.to_csv(output / "experiments.csv", index=False)
    pd.DataFrame(intervals).to_csv(output / "intervals.csv", index=False)
    ranking = summary.groupby("model").MAE.min()
    adjustable = ranking.drop(labels=BASELINES, errors="ignore")
    manifest = {"protocol_sha256":hashlib.sha256(config_bytes).hexdigest(),
                "dataset_sha256":hashlib.sha256(raw).hexdigest(), "seed":config["seed"],
                "code_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
                "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "dirty":bool(subprocess.check_output(["git","status","--porcelain"],text=True).strip()),
                "selection_exploratory":summary.iloc[0].experiment,
                "best_adjustable_exploratory":None if adjustable.empty else adjustable.idxmin(),
                "models":models,"budgets":budgets,"feature_sets":modes,
                "versions":{x:version(x) for x in ["numpy","pandas","scikit-learn","optuna","xgboost","statsmodels"]}}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
    print(summary.to_string(index=False),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=BASELINES+LEARNERS)
    parser.add_argument("--budgets", nargs="+", type=int, default=[10,30,60])
    parser.add_argument("--features", nargs="+", choices=["lag3","lag5","engineered"],default=["lag3"])
    args=parser.parse_args()
    if not set(args.models)<=set(BASELINES+LEARNERS+["CatBoost"]):
        parser.error("Modelo desconocido")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run(args.output,args.models,args.budgets,args.features)

