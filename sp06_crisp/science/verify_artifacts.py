"""Refit saved configurations from a clean checkout and compare archived predictions."""
import argparse
import json
import os
from pathlib import Path
import sys
import warnings
sys.path.insert(0,str(Path(__file__).parent.parent))

import numpy as np
import optuna
import pandas as pd
from protocol_v2 import read_data
from research import ROOT, baseline, features, learner, predict_model, BASELINES

parser=argparse.ArgumentParser()
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args()
data=read_data((ROOT/"wdi_mortality.csv").read_bytes())
reports=[]
with warnings.catch_warnings():
 warnings.simplefilter("ignore")
 for folder in ("baselines","ablations","trees","forest_both"):
  expected=pd.read_csv(ROOT/"science"/folder/"predictions.csv")
  for experiment,group in expected.groupby("experiment"):
   maximum=0
   total=0
   for year,observed in group.groupby("year"):
    first=observed.iloc[0]
    panel,columns=features(data,first.features)
    test=panel[panel.year==year]
    if first.model in BASELINES:
     actual=np.array([baseline(data,country,year,first.model) for country in test.iso3])
    else:
     params=json.loads(first.params)
     model=learner(first.model,optuna.trial.FixedTrial(params),606)
     train=panel[panel.year<year]
     y=train.delta if first.target=="difference" else np.log1p(train.probability_pct)
     model.fit(train[columns],y)
     actual=predict_model(model,test,columns,first.target)
    lookup=observed.set_index("iso3").forecast
    error=float(np.max(np.abs(actual-test.iso3.map(lookup).to_numpy())))
    maximum=max(maximum,error)
    total+=len(test)
   reports.append(dict(experiment=experiment,predictions=total,max_absolute_difference=maximum,
                       tolerance=1e-8,passed=maximum<=1e-8))
result=pd.DataFrame(reports)
args.output.parent.mkdir(parents=True,exist_ok=True)
result.to_csv(args.output,index=False)
print(result.to_string(index=False))
if not result.passed.all():raise SystemExit(1)
