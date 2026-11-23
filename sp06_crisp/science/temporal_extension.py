"""Execute the frozen WHO temporal extension on a homogeneous release."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import optuna
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent.parent))
from research import features,learner,predict_model
ROOT=Path(__file__).parent
OUT=ROOT/"final_audit"
protocol_path=OUT/"extension_protocol.json"
p=json.loads(protocol_path.read_text(encoding="utf-8-sig"))
countries=sorted(pd.read_csv(ROOT.parent/"wdi_mortality.csv").iso3.unique())
def fetch(country):
 query=urllib.parse.urlencode({"$filter":f"SpatialDim eq '{country}'","$top":1000})
 url="https://ghoapi.azureedge.net/api/NCDMORT3070?"+query
 response=json.load(urllib.request.urlopen(url,timeout=40))
 if "@odata.nextLink" in response:raise ValueError("Unexpected pagination")
 return {"url":url,"response":response}
archive=OUT/"who_release_raw.json"
if archive.exists():
 raw=archive.read_bytes()
 responses=json.loads(raw)
else:
 with ThreadPoolExecutor(max_workers=4) as pool:
  responses=list(pool.map(fetch,countries))
 raw=json.dumps(responses,ensure_ascii=False).encode("utf8")
 archive.write_bytes(raw)
records=[]
for row in [row for response in responses for row in response["response"]["value"]]:
 if row["Dim1"] != p["sex"]:continue
 if row["Dim2"] != p["age"]:raise ValueError("Unexpected age stratum")
 records.append({"iso3":row["SpatialDim"],"year":int(row["TimeDim"]),
                 "probability_pct":float(row["NumericValue"]),"record_date":row["Date"]})
data=pd.DataFrame(records).sort_values(["iso3","year"])
if data.duplicated(["iso3","year"]).any():raise ValueError("Duplicate WHO observations")
assert set(data.iso3)==set(countries)
assert data.probability_pct.between(0,100).all()
data.to_csv(OUT/"who_release_panel.csv",index=False)
rows,columns=features(data[["iso3","year","probability_pct"]],"lag5")
train=rows[rows.year<=p["train_last_year"]]
test=rows[rows.year.isin(p["test_years"])].copy()
assert len(test)==40
model=learner("Ridge",optuna.trial.FixedTrial({"alpha":p["alpha"]}),606)
model.fit(train[columns],train.delta)
test["forecast"]=predict_model(model,test,columns,"difference")
test["baseline"]=test.lag1
test["primary"]=test.iso3.ne("PER")
test[["iso3","year","forecast","baseline","primary"]].to_csv(OUT/"extension_frozen_predictions.csv",index=False)
test["error"]=(test.probability_pct-test.forecast).abs()
test["baseline_error"]=(test.probability_pct-test.baseline).abs()
test["delta_error"]=test.error-test.baseline_error
test.to_csv(OUT/"extension_evaluation.csv",index=False)
primary=test[test.primary]
country_delta=primary.groupby("iso3").delta_error.mean()
rng=np.random.default_rng(606)
interval=np.quantile(rng.choice(country_delta.to_numpy(),(5000,len(country_delta))).mean(axis=1),[.025,.975])
metrics={"countries":int(primary.iso3.nunique()),"cells":len(primary),
 "model_MAE":primary.error.mean(),"baseline_MAE":primary.baseline_error.mean(),
 "delta_MAE":country_delta.mean(),"CI_lower":interval[0],"CI_upper":interval[1],
 "countries_better_pct":100*country_delta.lt(0).mean(),
 "by_year":primary.groupby("year")[["error","baseline_error"]].mean().to_dict(),
 "excluded_PER":test[~test.primary][["year","probability_pct","forecast","baseline"]].to_dict("records"),
 "raw_sha256":hashlib.sha256(raw).hexdigest(),"protocol_sha256":hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
 "urls":[response["url"] for response in responses],"source_dates":sorted(data.record_date.unique())}
(OUT/"extension_metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps(metrics,ensure_ascii=False,indent=2))
