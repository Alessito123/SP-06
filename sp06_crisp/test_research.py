import unittest
import numpy as np
from pathlib import Path
from research import features, quantile, baseline
from protocol_v2 import read_data, PersistenceRegressor

class ResearchTest(unittest.TestCase):
 def setUp(self):
  self.data=read_data(Path(__file__).with_name("wdi_mortality.csv").read_bytes())
 def test_features_are_past_only(self):
  before,cols=features(self.data,"engineered")
  modified=self.data.copy()
  modified.loc[modified.year>=2016,"probability_pct"]=99
  after,_=features(modified,"engineered")
  self.assertTrue(before.query("year == 2016")[cols].equals(after.query("year == 2016")[cols]))
 def test_persistence(self):
  rows,cols=features(self.data,"lag3")
  model=PersistenceRegressor().fit(rows[cols])
  np.testing.assert_allclose(np.expm1(model.predict(rows)),rows.lag1)
 def test_baseline_has_no_future_access(self):
  original=baseline(self.data,"PER",2016,"Deriva amortiguada")
  modified=self.data.copy()
  modified.loc[modified.year>=2016,"probability_pct"]=99
  self.assertEqual(original,baseline(modified,"PER",2016,"Deriva amortiguada"))
 def test_quantile(self):
  self.assertEqual(quantile([1,2,3,4],.1,True),100)
 def test_units_and_duplicates(self):
  for text in ["iso3,year,probability_pct\nPER,2010,101\n",
               "iso3,year,probability_pct\nPER,2010,10\nPER,2010,11\n"]:
   with self.assertRaises(ValueError):read_data(text.encode())
