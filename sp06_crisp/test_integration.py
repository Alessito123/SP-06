"""End-to-end scientific reproducibility checks on the versioned dataset."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import optuna
import pandas as pd

from protocol_v2 import read_data
from research import ROOT, features, learner, predict_model, run


class IntegrationTest(unittest.TestCase):
    def test_archived_best_predictions_from_parameters(self):
        data = read_data((ROOT / "wdi_mortality.csv").read_bytes())
        rows, columns = features(data, "lag5")
        archived = pd.read_csv(ROOT / "science/ablations/predictions.csv")
        archived = archived[archived.experiment == "Ridge-lag5-difference-60"]
        for year, expected in archived.groupby("year"):
            params = json.loads(expected.params.iloc[0])
            train = rows[rows.year < year]
            test = rows[rows.year == year]
            model = learner("Ridge", optuna.trial.FixedTrial(params), 606)
            model.fit(train[columns], train.delta)
            actual = predict_model(model, test, columns, "difference")
            lookup = expected.set_index("iso3").forecast
            np.testing.assert_allclose(actual, test.iso3.map(lookup), rtol=1e-10, atol=1e-10)

    def test_optuna_cli_reproduces_across_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            for output in (first, second):
                subprocess.run(
                    [sys.executable, str(ROOT / "research.py"), "--output", str(output),
                     "--models", "Ridge", "--budgets", "1", "--features", "lag3"],
                    check=True, cwd=ROOT.parent, capture_output=True, text=True,
                )
            a = pd.read_csv(first / "predictions.csv")
            b = pd.read_csv(second / "predictions.csv")
            pd.testing.assert_frame_equal(a.drop(columns="duration"), b.drop(columns="duration"))
            intervals = pd.read_csv(first / "intervals.csv")
            self.assertTrue((intervals.calibration_last_year < intervals.year).all())
            noninformative = intervals[intervals.full_support_due_to_small_n]
            self.assertTrue(noninformative.width.eq(100).all())

    def test_versioned_artifacts_have_complete_evaluation_cells(self):
        for folder in ("baselines", "ablations", "trees", "forest_both"):
            frame = pd.read_csv(ROOT / "science" / folder / "predictions.csv")
            self.assertFalse(frame.duplicated(["experiment", "iso3", "year"]).any())
            self.assertTrue((frame.train_end < frame.year).all())
            self.assertTrue(frame.groupby("experiment").size().eq(120).all())
            self.assertTrue(frame.forecast.between(0, 100).all())


if __name__ == "__main__":
    unittest.main()
