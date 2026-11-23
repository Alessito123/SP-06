"""Recalculate interval outputs with the bounded-support finite-rank rule."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent.parent))
import research
import pandas as pd
import numpy as np
root=Path(__file__).parent
for folder in root.iterdir():
 if not (folder/"experiments.csv").exists():continue
 pred=pd.read_csv(folder/"predictions.csv")
 records=[]
 for experiment,group in pred.groupby("experiment"):
  for year in sorted(group.year.unique())[2:]:
   past=group[group.year<year]
   test=group[group.year==year]
   residuals=abs(past.observed-past.forecast)
   for method in ["empirical","pooled_conformal","year_block_conformal"]:
    values=residuals.groupby(past.year).max() if method=="year_block_conformal" else residuals
    corrected=method!="empirical"
    radius=research.quantile(values,.1,corrected)
    lo=(test.forecast-radius).clip(0,100)
    hi=(test.forecast+radius).clip(0,100)
    for idx,row in test.iterrows():
     records.append(dict(experiment=experiment,method=method,year=year,iso3=row.iso3,
       coverage=lo[idx]<=row.observed<=hi[idx],width=hi[idx]-lo[idx],nominal=.9,
       calibration_last_year=year-1,calibration_n=len(values),
       full_support_due_to_small_n=corrected and int(np.ceil((len(values)+1)*.9))>len(values)))
 pd.DataFrame(records).to_csv(folder/"intervals.csv",index=False)
 manifest=json.loads((folder/"manifest.json").read_text())
 manifest["interval_revision"]="bounded-support rule; see recalibrate.py and its source hash"
 manifest["interval_source_sha256"]=research.hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 (folder/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
 print(folder.name)
