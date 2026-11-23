"""Compile completed exploratory batches into scientific tables and figures."""
from pathlib import Path
import json
import pandas as pd
import altair as alt
import vl_convert as vlc

root=Path(__file__).parent
frames=[]
intervals=[]
predictions=[]
for name in ["baselines","ablations","trees","forest_both"]:
 path=root/name
 if (path/"experiments.csv").exists():
  frame=pd.read_csv(path/"experiments.csv")
  manifest=json.loads((path/"manifest.json").read_text())
  frame["code_commit"]=manifest["code_commit"]
  frame["source_sha256"]=manifest["source_sha256"]
  frame["dataset_sha256"]=manifest["dataset_sha256"]
  origin_params=pd.read_csv(path/"predictions.csv").groupby("experiment").apply(
      lambda group: json.dumps(group.groupby("year").params.first().to_dict(),ensure_ascii=False),
      include_groups=False)
  frame["parameters_by_origin"]=frame.experiment.map(origin_params)
  frames.append(frame)
  predictions.append(pd.read_csv(path/"predictions.csv"))
  intervals.append(pd.read_csv(path/"intervals.csv"))
if not frames:raise RuntimeError("No completed batches")
table=pd.concat(frames,ignore_index=True).sort_values("MAE")
table.to_csv(root/"comparison.csv",index=False)
detail=pd.concat(predictions,ignore_index=True)
detail["absolute_error"]=(detail.observed-detail.forecast).abs()
detail["delta_error"]=detail.absolute_error-(detail.observed-detail.baseline).abs()
for group in ["year","iso3"]:
 detail.groupby(["experiment",group]).agg(
     MAE=("absolute_error","mean"),delta_MAE=("delta_error","mean"),
     cells=("absolute_error","size")).reset_index().to_csv(root/f"errors_by_{group}.csv",index=False)
detail["period"]=detail.year.map(lambda year: "2013–2015" if year<=2015 else "2016–2018")
detail.groupby(["experiment","period"]).agg(
    MAE=("absolute_error","mean"),delta_MAE=("delta_error","mean")).reset_index().to_csv(
        root/"stability_by_period.csv",index=False)
band=pd.concat(intervals,ignore_index=True)
for group in ["year","iso3"]:
 band.groupby(["experiment","method",group]).agg(coverage=("coverage","mean"),width=("width","mean"),
      cells=("coverage","size")).reset_index().to_csv(root/f"coverage_by_{group}.csv",index=False)
best=table.loc[table.groupby("model").MAE.idxmin()]
chart=alt.Chart(best).mark_point(filled=True,size=90,color="#087e8b").encode(
 x=alt.X("delta_MAE:Q",title="Diferencia MAE frente a persistencia (pp)"),
 y=alt.Y("model:N",title="Modelo",sort="x"),
 tooltip=["experiment","MAE","RMSE","MASE","delta_MAE","CI_lower","CI_upper"])
bars=alt.Chart(best).mark_rule(color="#087e8b").encode(x="CI_lower:Q",x2="CI_upper:Q",y=alt.Y("model:N",sort="x"))
for name,visual in [("model_comparison",bars+chart),
 ("budget_comparison",alt.Chart(table[table.budget.gt(0)]).mark_line(point=True).encode(
 x=alt.X("budget:O",title="Ensayos"),y=alt.Y("MAE:Q",title="MAE (pp)"),
 color="model:N",column="target:N",detail=["features"]))]:
 (root/f"{name}.html").write_text(visual.to_html(),encoding="utf8")
 (root/f"{name}.png").write_bytes(vlc.vegalite_to_png(visual.properties(width=430,height=230).to_dict(),scale=2))
print(table.head(12).to_string(index=False))
