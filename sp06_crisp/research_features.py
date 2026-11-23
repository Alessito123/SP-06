"""Scientific experiment components used by the rolling-origin runner."""
import numpy as np
import pandas as pd


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
