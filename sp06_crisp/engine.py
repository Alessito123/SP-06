"""Persist and serve local SP-06 models without running training."""
import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

import numpy as np
import pandas as pd
import skops.io
from skops.io.exceptions import UntrustedTypesFoundException
from xgboost import XGBRegressor

from modeling import FEATURES

RUNS = Path(__file__).with_name("runs")
LIBRARIES = ("numpy", "pandas", "scikit-learn", "xgboost", "skops", "optuna")


def save_run(model, metadata, tables):
    run = str(uuid4())
    RUNS.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=RUNS) as temp:
        staging = Path(temp) / run
        staging.mkdir()
        model_path = staging / ("model.json" if metadata["model"] == "XGBoost" else "model.skops")
        if metadata["model"] == "XGBoost":
            model.save_model(model_path)
        else:
            skops.io.dump(model, model_path)
        manifest = {
            **metadata, "id": run, "features": FEATURES, "target": "log1p(probability_pct)",
            "versions": {name: version(name) for name in LIBRARIES},
            "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        for name, table in tables.items():
            (staging / f"{name}.json").write_text(table.to_json(orient="records", force_ascii=False), encoding="utf-8")
        staging.rename(RUNS / run)
    return run


def manifest_for(run):
    folder = RUNS / str(UUID(run))
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest["id"] != str(UUID(run)) or manifest["features"] != FEATURES:
        raise ValueError("El manifiesto de la corrida no coincide con el motor.")
    return folder, manifest


def list_runs(fingerprint):
    if not RUNS.exists():
        return []
    available = []
    for folder in RUNS.iterdir():
        try:
            _, manifest = manifest_for(folder.name)
            if manifest["dataset_sha256"] == fingerprint:
                available.append(manifest)
        except (OSError, ValueError, KeyError):
            continue
    return sorted(available, key=lambda manifest: manifest["created"], reverse=True)


def load_run(run):
    folder, manifest = manifest_for(run)
    if any(version(name) != installed for name, installed in manifest["versions"].items()):
        raise ValueError("Las versiones de dependencias difieren de la corrida guardada.")
    xgb = manifest["model"] == "XGBoost"
    model_path = folder / ("model.json" if xgb else "model.skops")
    payload = model_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != manifest["model_sha256"]:
        raise ValueError("El archivo del modelo no coincide con su huella.")
    if xgb:
        model = XGBRegressor()
        model.load_model(bytearray(payload))
    else:
        # Runs are written by this application. No model uploads are accepted.
        trusted = ["sklearn.tree._tree.Tree"] if manifest["model"] == "Random Forest" else []
        try:
            model = skops.io.loads(payload, trusted=trusted)
        except UntrustedTypesFoundException as error:
            raise ValueError("El artefacto contiene un tipo que el motor no admite.") from error
    tables = {name: pd.DataFrame(json.loads((folder / f"{name}.json").read_text(encoding="utf-8")))
              for name in ("folds", "scores", "trials")}
    return model, manifest, tables


def forecast(model, manifest, history, year):
    """Predict from the three observed years immediately preceding the target."""
    if year <= manifest["cutoff"]:
        raise ValueError("El año objetivo debe ser posterior al corte del modelo.")
    needed = [year - lag for lag in range(1, 4)]
    if any(prior not in history for prior in needed):
        raise ValueError(f"Se requieren los valores observados de {year - 3} a {year - 1}.")
    values = [float(history[prior]) for prior in needed]
    if not all(0 <= value <= 100 for value in values):
        raise ValueError("Los rezagos deben ser porcentajes entre 0 y 100.")
    features = pd.DataFrame([values], columns=FEATURES)
    log_value = float(model.predict(features)[0])
    value = float(np.clip(np.expm1(log_value), 0, 100))
    radius = manifest["radius"]
    return {"year": year, "pronóstico": value, "persistencia": values[0],
            "inferior": max(0.0, value - radius), "superior": min(100.0, value + radius)}, features


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", help="Identificador de la corrida guardada")
    parser.add_argument("country", help="Código ISO del país")
    parser.add_argument("year", type=int)
    parser.add_argument("--csv", type=Path, default=Path(__file__).with_name("wdi_mortality.csv"))
    args = parser.parse_args()
    from protocol_v2 import read_data

    model, manifest, _ = load_run(args.run)
    raw = args.csv.read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["dataset_sha256"]:
        parser.error("El CSV no corresponde al dataset de la corrida.")
    panel = read_data(raw)
    history = panel[panel.iso3 == args.country.upper()].set_index("year").probability_pct.to_dict()
    try:
        prediction, _ = forecast(model, manifest, history, args.year)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({"country": args.country.upper(), "run": args.run, **prediction}, ensure_ascii=False))
