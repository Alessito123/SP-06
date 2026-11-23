"""Scientific experiment components used by the rolling-origin runner."""
import numpy as np
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from xgboost import XGBRegressor


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
