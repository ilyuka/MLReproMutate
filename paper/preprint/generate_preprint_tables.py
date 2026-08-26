#!/usr/bin/env python3

import csv
from pathlib import Path

PREPRINT = Path(__file__).resolve().parent
ROOT = PREPRINT.parents[1]
SOURCE = ROOT / "paper" / "tables"
OUT = PREPRINT / "tables"

OUT.mkdir(parents=True, exist_ok=True)


def read_csv(name):
    with (SOURCE / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def esc(value):
    return (
        str(value)
        .replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
    )


def pct_count(n, pct):
    return f"{n} ({pct}\\%)"


study = read_csv("study_summary.csv")
operators = read_csv("operator_results.csv")
d027 = read_csv("d027_restoration.csv")


# ------------------------------------------------------------
# Table 1 — study executability
# ------------------------------------------------------------

lines = [
    r"\begin{table}[t]",
    r"\centering",
    r"\caption{Executability before and after bounded restoration. "
    r"Non-evaluable cases remain part of the frozen 39-case study frame.}",
    r"\label{tab:study-summary}",
    r"\vspace{0.35em}",
    r"\small",
    r"\renewcommand{\arraystretch}{1.28}",
    r"\setlength{\tabcolsep}{10pt}",
    r"\begin{tabular}{lrrr}",
    r"\toprule",
    r"\addlinespace[2pt]",
    r"\textbf{Layer} & "
    r"\textbf{Selected} & "
    r"\textbf{Evaluated, n (\%)} & "
    r"\textbf{Non-evaluable, n (\%)} \\",
    r"\addlinespace[2pt]",
    r"\midrule",
    r"\addlinespace[3pt]",
]

for row in study:
    layer = esc(row["layer"])

    evaluated = (
        f"{row['evaluated']} "
        f"({row['evaluated_percent']}\\%)"
    )

    non_evaluable = (
        f"{row['non_evaluable']} "
        f"({row['non_evaluable_percent']}\\%)"
    )

    if row["layer"].startswith("Combined"):
        layer = rf"\textbf{{{layer}}}"
        evaluated = rf"\textbf{{{evaluated}}}"
        non_evaluable = rf"\textbf{{{non_evaluable}}}"

    lines.append(
        f"{layer} & "
        f"{row['selected']} & "
        f"{evaluated} & "
        f"{non_evaluable} \\\\"
    )

    lines.append(r"\addlinespace[3pt]")

lines += [
    r"\bottomrule",
    r"\end{tabular}",
    r"\vspace{0.25em}",
    r"\end{table}",
    "",
]

(OUT / "table_study_summary.tex").write_text(
    "\n".join(lines),
    encoding="utf-8",
)


# ------------------------------------------------------------
# Table 2 — B02 operator results
# ------------------------------------------------------------

lines = [
    r"\begin{table}[t]",
    r"\centering",
    r"\caption{Combined B02 results by mutation operator. "
    r"Detection is reported over confirmed non-equivalent evaluated "
    r"mutations; confirmed-equivalent evaluations are excluded.}",
    r"\label{tab:operator-results}",
    r"\small",
    r"\renewcommand{\arraystretch}{1.18}",
    r"\setlength{\tabcolsep}{4.5pt}",
    r"\begin{tabular}{lrrrrrrr}",
    r"\toprule",
    r"\textbf{Operator} & "
    r"\textbf{Selected} & "
    r"\textbf{Evaluated} & "
    r"\textbf{Non-evaluable} & "
    r"\textbf{\textsc{Killed}} & "
    r"\textbf{\textsc{Survived}} & "
    r"\textbf{\textsc{Equivalent}} & "
    r"\textbf{Detection} \\",
    r"\midrule",
]

for row in operators:
    killed = int(row["killed"])

    detection = (
        f"{row['detection_numerator']}/"
        f"{row['detection_denominator']} "
        f"({row['detection_percent']}\\%)"
    )

    if killed:
        killed_cell = rf"\textbf{{{killed}}}"
        detection_cell = rf"\textbf{{{detection}}}"
    else:
        killed_cell = str(killed)
        detection_cell = detection

    lines.append(
        rf"\texttt{{{esc(row['operator'])}}} & "
        f"{row['selected']} & "
        f"{row['evaluated']} & "
        f"{row['non_evaluable']} & "
        f"{killed_cell} & "
        f"{row['survived']} & "
        f"{row['equivalent']} & "
        f"{detection_cell} \\\\"
    )

lines += [
    r"\bottomrule",
    r"\end{tabular}",
    r"\end{table}",
    "",
]

(OUT / "table_operator_results.tex").write_text(
    "\n".join(lines),
    encoding="utf-8",
)


# ------------------------------------------------------------
# Appendix / restoration table
# ------------------------------------------------------------

lines = [
    r"\begin{table}[t]",
    r"\centering",
    r"\caption{D027 bounded-restoration accounting. "
    r"Report presence and substantive restoration attempt are distinct.}",
    r"\label{tab:d027-accounting}",
    r"\small",
    r"\renewcommand{\arraystretch}{1.18}",
    r"\setlength{\tabcolsep}{7pt}",
    r"\begin{tabular}{lrr}",
    r"\toprule",
    r"\textbf{State} & "
    r"\textbf{Count} & "
    r"\textbf{\% of cohort} \\",
    r"\midrule",
]

for row in d027:
    lines.append(
        f"{esc(row['state'])} & "
        f"{row['count']} & "
        f"{row['percent_of_cohort']}\\% \\\\"
    )

lines += [
    r"\bottomrule",
    r"\end{tabular}",
    r"\end{table}",
    "",
]

(OUT / "table_d027_restoration.tex").write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print("Preprint tables: OK")
for p in sorted(OUT.glob("*.tex")):
    print(" ", p.relative_to(PREPRINT))