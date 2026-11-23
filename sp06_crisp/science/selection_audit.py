"""Conditional sensitivity to experiment selection and temporal dependence."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).parent
OUT=ROOT/"final_audit"
OUT.mkdir(exist_ok=True)
parts=[]
for name in ("baselines","ablations","trees","forest_both"):
 parts.append(pd.read_csv(ROOT/name/"predictions.csv"))
data=pd.concat(parts,ignore_index=True)
data["delta"]=(data.observed-data.forecast).abs()-(data.observed-data.baseline).abs()
countries=sorted(data.iso3.unique())
years=sorted(data.year.unique())
experiments=sorted(data.experiment.unique())
indexed=data.set_index(["iso3","year","experiment"]).delta
cube=indexed.reindex(pd.MultiIndex.from_product([countries,years,experiments])).to_numpy().reshape(
 len(countries),len(years),len(experiments))
assert np.isfinite(cube).all()
means=cube.mean(axis=(0,1))
rows=[]
for block in (1,2,3):
 rng=np.random.default_rng(606)
 n=5000
 country_weights=rng.multinomial(len(countries),np.repeat(1/len(countries),len(countries)),size=n)/len(countries)
 time_weights=np.zeros((n,len(years)))
 for replicate in range(n):
  starts=rng.integers(0,len(years)-block+1,size=int(np.ceil(len(years)/block)))
  sample=np.concatenate([np.arange(start,start+block) for start in starts])[:len(years)]
  time_weights[replicate]=np.bincount(sample,minlength=len(years))/len(years)
 samples=np.einsum("bi,ijm,bj->bm",country_weights,cube,time_weights,optimize=True)
 centered=samples-samples.mean(axis=0)
 critical=np.quantile(np.max(np.abs(centered),axis=1),.95)
 for idx,experiment in enumerate(experiments):
  rows.append(dict(experiment=experiment,block_years=block,delta_MAE=means[idx],
                   simultaneous_lower=means[idx]-critical,simultaneous_upper=means[idx]+critical,
                   resamples=n,experiments_in_family=len(experiments)))
pd.DataFrame(rows).to_csv(OUT/"selection_temporal_sensitivity.csv",index=False)
table=pd.read_csv(ROOT/"comparison.csv")
common=table[(table.features=="lag3") & ((table.budget==10) | (table.budget==0))]
common.to_csv(OUT/"common_budget_10.csv",index=False)
best=table.iloc[0].experiment
print(pd.DataFrame(rows).query("experiment == @best").to_string(index=False))
print("All intervals conditional on observed fitted predictions, six years only.")
