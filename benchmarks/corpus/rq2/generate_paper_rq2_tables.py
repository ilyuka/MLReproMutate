#!/usr/bin/env python3
"""Generate tables-only RQ2 manuscript assets from frozen result CSVs."""

from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
OUT = ROOT / "paper_assets"

WF = RESULTS / "rq2_workflow_kind.csv"
OR = RESULTS / "rq2_b02_oracle_kind.csv"
OO = RESULTS / "rq2_b02_operator_oracle.csv"
AT = RESULTS / "rq2_evaluability_by_category.csv"

WF_ORDER = ["upstream-test","ci","documented-validation","documented-experiment","documented-example"]
OR_ORDER = ["assertion","completion-only"]
OP_ORDER = ["random-seed","dependency-pin","data-split","cv-fold-count"]

def rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def idx(xs, key):
    return {x[key]: x for x in xs}

def n(row, key):
    return int(row[key])

def pretty(s):
    return "CI" if s == "ci" else s

def rate(k, total):
    return "—" if total == 0 else f"{100*k/total:.1f}%"

def tex(s):
    return s.replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")

def sha(path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def validate(wf, oracle, oo, attr):
    wi, oi = idx(wf, "workflow_kind"), idx(oracle, "oracle_kind")
    if sum(n(wi[x],"evaluated_confirmed_non_equivalent") for x in WF_ORDER) != 23:
        raise SystemExit("workflow N changed")
    if sum(n(wi[x],"killed") for x in WF_ORDER) != 2:
        raise SystemExit("workflow killed total changed")
    if sum(n(wi[x],"survived") for x in WF_ORDER) != 21:
        raise SystemExit("workflow survived total changed")
    if sum(n(oi[x],"evaluated_confirmed_non_equivalent") for x in OR_ORDER) != 15:
        raise SystemExit("oracle N changed")
    if sum(n(oi[x],"killed") for x in OR_ORDER) != 2:
        raise SystemExit("oracle killed total changed")
    dep = [x for x in oo if x["operator"]=="dependency-pin" and x["oracle_kind"]=="completion-only"]
    if len(dep)!=1 or (n(dep[0],"meaningful_n"),n(dep[0],"killed"),n(dep[0],"survived")) != (3,2,1):
        raise SystemExit("dependency-pin/completion-only diagnostic cell changed")
    ai = {x["category"]:x for x in attr if x["dimension"]=="oracle_kind" and x["scope"]=="B02-prospective"}
    if (n(ai["assertion"],"selected"),n(ai["assertion"],"combined_evaluated"),n(ai["assertion"],"meaningful_n")) != (7,3,2):
        raise SystemExit("assertion attrition changed")
    if (n(ai["completion-only"],"selected"),n(ai["completion-only"],"combined_evaluated"),n(ai["completion-only"],"meaningful_n")) != (22,13,13):
        raise SystemExit("completion-only attrition changed")

def write_pair(name, headers, body, caption, label):
    md = ["| " + " | ".join(headers) + " |",
          "|" + "|".join(["---"] + ["---:"]*(len(headers)-1)) + "|"]
    md += ["| " + " | ".join(map(str, r)) + " |" for r in body]
    (OUT/f"{name}.md").write_text("\n".join(md)+"\n", encoding="utf-8")

    aligns = "l" + "r"*(len(headers)-1)
    tx = [
        r"\begin{table}[t]", r"\centering",
        rf"\caption{{{caption}}}", rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{aligns}}}", r"\toprule",
        " & ".join(tex(x) for x in headers) + r" \\",
        r"\midrule",
    ]
    tx += [" & ".join(tex(str(x)) for x in r) + r" \\" for r in body]
    tx += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    (OUT/f"{name}.tex").write_text("\n".join(tx), encoding="utf-8")

def main():
    wf, oracle, oo, attr = rows(WF), rows(OR), rows(OO), rows(AT)
    validate(wf, oracle, oo, attr)
    OUT.mkdir(parents=True, exist_ok=True)

    # Delete superseded graph if an earlier generator created it.
    old = OUT / "figure_rq2_workflow_oracle.png"
    if old.exists():
        old.unlink()

    wi, oi = idx(wf,"workflow_kind"), idx(oracle,"oracle_kind")

    body = []
    for x in WF_ORDER:
        r=wi[x]; total=n(r,"evaluated_confirmed_non_equivalent"); k=n(r,"killed"); s=n(r,"survived")
        body.append([pretty(x),total,k,s,rate(k,total)])
    write_pair(
        "table_rq2_workflow_kind",
        ["Workflow type","N","Killed","Survived","Detection"],
        body,
        "Detection of confirmed non-equivalent mutations by frozen validation-workflow type. Workflow type is categorical; no ordinal ranking is assumed.",
        "tab:rq2-workflow",
    )

    body = []
    for x in OR_ORDER:
        r=oi[x]; total=n(r,"evaluated_confirmed_non_equivalent"); k=n(r,"killed"); s=n(r,"survived")
        body.append([pretty(x),total,k,s,rate(k,total)])
    write_pair(
        "table_rq2_oracle_kind",
        ["Oracle kind","N","Killed","Survived","Detection"],
        body,
        "Detection by prospectively recorded validation-oracle kind in B02. B01 is excluded because schema version 1 did not prospectively record oracle kind.",
        "tab:rq2-oracle",
    )

    order={(op,o):i for i,(op,o) in enumerate((op,o) for op in OP_ORDER for o in OR_ORDER)}
    pop=[r for r in oo if n(r,"meaningful_n")>0]
    pop.sort(key=lambda r: order[(r["operator"],r["oracle_kind"])])
    body=[[pretty(r["operator"]),pretty(r["oracle_kind"]),n(r,"meaningful_n"),n(r,"killed"),n(r,"survived")] for r in pop]
    write_pair(
        "table_rq2_operator_oracle",
        ["Operator","Oracle kind","N","Killed","Survived"],
        body,
        "Operator composition of the prospective B02 oracle analysis. Both detected mutations occurred in the dependency-pin/completion-only cell; sparse cells prevent attribution of this pattern to oracle kind.",
        "tab:rq2-operator-oracle",
    )

    ai={r["category"]:r for r in attr if r["dimension"]=="oracle_kind" and r["scope"]=="B02-prospective"}
    body=[[pretty(x),n(ai[x],"selected"),n(ai[x],"combined_evaluated"),n(ai[x],"meaningful_n")] for x in OR_ORDER]
    write_pair(
        "table_rq2_attrition",
        ["Oracle kind","Selected","Combined evaluated","Meaningful"],
        body,
        "Evaluability of prospectively classified B02 oracle categories.",
        "tab:rq2-oracle-attrition",
    )

    files=[WF,OR,OO,AT]
    outs=sorted(p for p in OUT.iterdir() if p.suffix in {".md",".tex"})
    manifest={
        "presentation":"tables-only",
        "figures_generated":False,
        "inputs":{str(p.relative_to(ROOT)):sha(p) for p in files},
        "outputs":{str(p.relative_to(ROOT)):sha(p) for p in outs},
    }
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print("RQ2 paper tables: OK")
    print("presentation: tables-only")
    for p in outs:
        print(" ", p.relative_to(ROOT))
    print(" ", (OUT/"manifest.json").relative_to(ROOT))

if __name__ == "__main__":
    main()
