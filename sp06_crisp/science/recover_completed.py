"""Recover fully completed experiments from an interrupted batch without rerunning."""
from pathlib import Path
import sys,json,textwrap
sys.path.insert(0,str(Path(__file__).parent.parent))
import research
import pandas as pd
output=Path(__file__).parent/"forest"
output.mkdir(exist_ok=False)
source=Path(__file__).parent/"trees-interrupted"
data=pd.read_csv(source/"predictions.csv")
counts=data.groupby("experiment").year.nunique()
completed=counts[counts==6].index
records=data[data.experiment.isin(completed)].to_dict("records")
pd.DataFrame(records).to_csv(output/"predictions.csv",index=False)
raw=(research.ROOT/"wdi_mortality.csv").read_bytes()
config_bytes=research.CONFIG.read_bytes()
config=json.loads(config_bytes.decode("utf-8-sig"))
body=Path(research.__file__).read_text(encoding="utf-8-sig")
segment=body[body.index("    predictions = pd.DataFrame(records)"):body.index('\n\n\nif __name__')]
context=dict(vars(research))
context.update(dict(output=output,records=records,raw=raw,config_bytes=config_bytes,config=config,
                    models=["Random Forest"],budgets=[10],modes=["lag3"]))
exec(textwrap.dedent(segment),context)
with (output/"trials.jsonl").open("w",encoding="utf8") as target:
 for line in (source/"trials.jsonl").read_text().splitlines():
  if json.loads(line)["experiment"] in completed:target.write(line+"\n")
