import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
import optuna
from sklearn.model_selection import GroupKFold

import engine
from protocol_v2 import SPACES, calibrate, evaluate_nested, forecast_metrics, outer_partitions, read_data, split_panel


class TrainingProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = Path(engine.__file__).with_name("wdi_mortality.csv").read_bytes()
        cls.frame = read_data(cls.content)
        cls.calendar, cls.blocks = split_panel(cls.frame)

    def test_calendar_and_group_boundaries(self):
        self.assertEqual([len(block) for block in self.blocks.values()], [260, 60, 60])
        folds = list(outer_partitions(self.blocks["Desarrollo"]))
        self.assertEqual(len(folds), 5)
        seen = set()
        for train, validation in folds:
            self.assertEqual((len(train), len(validation)), (160, 12))
            self.assertEqual((train.year.min(), train.year.max()), (2003, 2012))
            self.assertEqual((validation.year.min(), validation.year.max()), (2013, 2015))
            self.assertFalse(set(train.iso3) & set(validation.iso3))
            self.assertFalse(seen & set(validation.iso3))
            seen.update(validation.iso3)
            for fit, score in GroupKFold(3).split(train, groups=train.iso3):
                self.assertFalse(set(train.iloc[fit].iso3) & set(train.iloc[score].iso3))
        self.assertEqual(len(seen), 20)

    def test_future_changes_cannot_modify_development_features(self):
        changed = self.frame.copy()
        changed.loc[changed.year >= 2016, "probability_pct"] = 99
        _, blocks = split_panel(changed)
        self.assertTrue(blocks["Desarrollo"].equals(self.blocks["Desarrollo"]))

    def test_mase_uses_training_scale_for_unseen_countries(self):
        train, validation = next(outer_partitions(self.blocks["Desarrollo"]))
        expected = abs(validation.probability_pct - validation.lag1).mean() / abs(
            train.probability_pct - train.lag1
        ).mean()
        result = forecast_metrics(validation, np.log1p(validation.lag1.to_numpy()), train)
        self.assertAlmostEqual(result["MASE"], expected)

    def test_train_calibrate_reload_and_predict(self):
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        settings = {"models": ["Ridge"], "seed": 606, "trials": 1, "timeout": 60, "spaces": SPACES}
        development = self.blocks["Desarrollo"]
        model, name, params, folds, scores, trials = evaluate_nested(development, settings, lambda *_: None)
        self.assertEqual(len(scores), 10)
        self.assertEqual(name, scores.groupby("modelo")["MAE log"].mean().idxmin())
        self.assertIn(len(trials), (5, 6))
        self.assertTrue({"MAE log", "MAE (pp)", "RMSE (pp)", "MASE"} <= set(scores.columns))
        metadata = {"model": name, "params": params, "cutoff": 2015,
                    "radius": calibrate(model, self.blocks["Validación"])}
        history = self.frame.query("iso3 == 'PER'").set_index("year").probability_pct.to_dict()
        expected, _ = engine.forecast(model, metadata, history, 2022)
        with TemporaryDirectory() as tmp, patch.object(engine, "RUNS", Path(tmp)):
            run = engine.save_run(model, metadata, {"folds": folds, "scores": scores, "trials": trials})
            restored, manifest, _ = engine.load_run(run)
            actual, _ = engine.forecast(restored, manifest, history, 2022)
        self.assertEqual(actual, expected)
        with self.assertRaises(ValueError):
            engine.forecast(model, metadata, {2021: 12, 2020: 13}, 2022)
