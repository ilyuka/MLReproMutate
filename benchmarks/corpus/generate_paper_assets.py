#!/usr/bin/env python3
"""Generate paper-ready tables and figures from frozen final accounting."""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.corpus.final_accounting import AccountingError, calculate

ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "paper" / "tables"
FIGURE_DIR = ROOT / "paper" / "figures"
RESULTS_NUMBERS = ROOT / "paper" / "results_numbers.md"
OPERATORS = ("random-seed", "dependency-pin", "data-split", "cv-fold-count")
EXPECTED_FILES = (
    TABLE_DIR / "study_summary.csv",
    TABLE_DIR / "operator_results.csv",
    TABLE_DIR / "d027_restoration.csv",
    TABLE_DIR / "results_tables.md",
    TABLE_DIR / "results_tables.tex",
    FIGURE_DIR / "evaluability_primary_vs_combined.png",
    FIGURE_DIR / "evaluability_primary_vs_combined.pdf",
    FIGURE_DIR / "b02_outcomes_by_operator.png",
    FIGURE_DIR / "b02_outcomes_by_operator.pdf",
    FIGURE_DIR / "d027_restoration_accounting.png",
    FIGURE_DIR / "d027_restoration_accounting.pdf",
    RESULTS_NUMBERS,
)


def percent(numerator: int, denominator: int) -> str:
    return f"{100.0 * numerator / denominator:.1f}"


def _frozen_assertions(result: dict[str, Any]) -> None:
    expected = {
        "primary": (39, 13), "combined": (39, 24),
        "b02_primary": (29, 6), "b02_combined": (29, 16),
    }
    for key, pair in expected.items():
        summary = result[key]
        observed = summary["selected"], summary["evaluated"]
        if observed != pair:
            raise AccountingError(f"paper-assets frozen check {key}: {observed} != {pair}")
    combined = result["combined"]
    if tuple(combined[key] for key in ("non-evaluable", "survived", "killed", "equivalent")) != (15, 21, 2, 1):
        raise AccountingError("paper-assets frozen check: combined outcomes changed")
    operator_expected = {
        "random-seed": (10, 5, 5, 0, 0, 5),
        "dependency-pin": (10, 4, 1, 2, 1, 6),
        "data-split": (6, 4, 4, 0, 0, 2),
        "cv-fold-count": (3, 3, 3, 0, 0, 0),
    }
    for operator, values in operator_expected.items():
        summary = result["b02_by_operator"][operator]
        observed = tuple(summary[key] for key in
                         ("selected", "evaluated", "survived", "killed", "equivalent", "non-evaluable"))
        if observed != values:
            raise AccountingError(f"paper-assets frozen check {operator}: {observed} != {values}")
    d = result["d027"]
    d_values = tuple(d[key] for key in (
        "cohort", "report_present", "report_absent_not_attempted",
        "substantive_restoration_attempted", "restoration_not_attempted",
        "restored", "not_restored", "mutation_evaluated"))
    if d_values != (24, 19, 5, 18, 1, 11, 7, 11):
        raise AccountingError(f"paper-assets frozen check D027: {d_values}")
    detection = result["confirmed_detection"]
    if (detection["killed"], detection["confirmed_non_equivalent_survived"],
            detection["denominator"]) != (2, 21, 23):
        raise AccountingError("paper-assets frozen check: confirmed detection changed")


def build_rows(result: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    study = []
    for label, key in (("Primary execution", "primary"),
                       ("Combined primary + D027", "combined")):
        s = result[key]
        study.append({"layer": label, "selected": s["selected"], "evaluated": s["evaluated"],
                      "evaluated_percent": percent(s["evaluated"], s["selected"]),
                      "non_evaluable": s["non-evaluable"],
                      "non_evaluable_percent": percent(s["non-evaluable"], s["selected"]),
                      "survived": s["survived"], "killed": s["killed"],
                      "equivalent": s["equivalent"]})

    operator_rows = []
    b02_cases = [case for case in result["cases"] if case["batch"] == "B02"]
    for operator in OPERATORS:
        s = result["b02_by_operator"][operator]
        cases = [case for case in b02_cases if case["operator"] == operator]
        confirmed_survived = sum(
            case["combined_outcome"] == "survived"
            and case["combined_semantic_status"] == "confirmed-non-equivalent"
            for case in cases)
        numerator = s["killed"]
        denominator = numerator + confirmed_survived
        operator_rows.append({
            "operator": operator, "selected": s["selected"], "evaluated": s["evaluated"],
            "evaluated_percent": percent(s["evaluated"], s["selected"]),
            "non_evaluable": s["non-evaluable"], "survived": s["survived"],
            "killed": s["killed"], "equivalent": s["equivalent"],
            "confirmed_non_equivalent_evaluated": denominator,
            "detection_numerator": numerator, "detection_denominator": denominator,
            "detection_percent": percent(numerator, denominator),
        })

    d = result["d027"]
    d027_specs = (
        ("Cohort", "cohort"),
        ("Report/assessment present", "report_present"),
        ("No D027 report", "report_absent_not_attempted"),
        ("Substantive restoration attempted", "substantive_restoration_attempted"),
        ("Report present, restoration not attempted", "restoration_not_attempted"),
        ("Restored", "restored"),
        ("Not restored after substantive attempt", "not_restored"),
        ("Mutation evaluated", "mutation_evaluated"),
    )
    d027_rows = [{"state": label, "count": d[key], "percent_of_cohort": percent(d[key], d["cohort"])}
                 for label, key in d027_specs]
    return study, operator_rows, d027_rows


def _csv_text(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _markdown_table(rows: list[dict[str, Any]], headings: Iterable[str] | None = None) -> str:
    keys = list(rows[0])
    labels = list(headings or keys)
    lines = ["| " + " | ".join(labels) + " |", "| " + " | ".join("---" for _ in keys) + " |"]
    lines.extend("| " + " | ".join(str(row[key]) for key in keys) + " |" for row in rows)
    return "\n".join(lines)


def _latex(value: Any) -> str:
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
                    "$": r"\$", "#": r"\#", "_": r"\_",
                    "{": r"\{", "}": r"\}"}
    return "".join(replacements.get(character, character) for character in str(value))


def _latex_table(caption: str, rows: list[dict[str, Any]]) -> str:
    keys = list(rows[0])
    alignment = "l" + "r" * (len(keys) - 1)
    header = " & ".join(_latex(key.replace("_", " ")) for key in keys) + r" \\"
    body = "\n".join(" & ".join(_latex(row[key]) for key in keys) + r" \\" for row in rows)
    return ("\\begin{table}[ht]\n\\centering\n"
            f"\\caption{{{_latex(caption)}}}\n\\begin{{tabular}}{{{alignment}}}\n\\hline\n"
            f"{header}\n\\hline\n{body}\n\\hline\n\\end{{tabular}}\n\\end{{table}}")


def _write_text_assets(study: list[dict[str, Any]], operators: list[dict[str, Any]],
                       d027: list[dict[str, Any]], result: dict[str, Any]) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    (TABLE_DIR / "study_summary.csv").write_text(_csv_text(study), encoding="utf-8")
    (TABLE_DIR / "operator_results.csv").write_text(_csv_text(operators), encoding="utf-8")
    (TABLE_DIR / "d027_restoration.csv").write_text(_csv_text(d027), encoding="utf-8")
    md = """# Generated results tables

Table 1. Study summary. Outcome columns count cases in the full intended frame; confirmed detection uses a separate confirmed-non-equivalent denominator.

{study}

Table 2. B02 operator results. Detection denominators exclude confirmed-equivalent evaluations. Counts are small and uneven; the table does not establish meaningful statistical differences between operators.

{operators}

Table 3. D027 restoration accounting. Report present does not imply a substantive restoration attempt, and not attempted does not mean restoration failed.

{d027}
""".format(study=_markdown_table(study), operators=_markdown_table(operators), d027=_markdown_table(d027))
    (TABLE_DIR / "results_tables.md").write_text(md, encoding="utf-8")
    tex = "\n\n".join((
        _latex_table("Study summary. Outcome counts use the full intended frame; confirmed detection uses a separate non-equivalent denominator.", study),
        _latex_table("B02 operator results. Confirmed-equivalent evaluations are excluded from detection denominators.", operators),
        _latex_table("D027 restoration accounting. Report presence and substantive restoration attempt are distinct.", d027),
    )) + "\n"
    (TABLE_DIR / "results_tables.tex").write_text(tex, encoding="utf-8")
    primary, combined = result["primary"], result["combined"]
    b02_primary, b02_combined = result["b02_primary"], result["b02_combined"]
    detection = result["confirmed_detection"]
    lines = [
        "# Generated results numbers", "",
        "These numbers are generated from final_accounting.py and should not be edited manually.", "",
        f"- Frozen frame: {result['totals']['selected']} repositories.",
        f"- Primary mutation evaluation: {primary['evaluated']}/{primary['selected']} "
        f"({percent(primary['evaluated'], primary['selected'])}%).",
        f"- Combined available evaluation: {combined['evaluated']}/{combined['selected']} "
        f"({percent(combined['evaluated'], combined['selected'])}%).",
        f"- B02 primary: {b02_primary['evaluated']}/{b02_primary['selected']} "
        f"({percent(b02_primary['evaluated'], b02_primary['selected'])}%).",
        f"- B02 combined: {b02_combined['evaluated']}/{b02_combined['selected']} "
        f"({percent(b02_combined['evaluated'], b02_combined['selected'])}%).",
        f"- Confirmed-non-equivalent evaluated mutations: {detection['denominator']}.",
        f"- Observed in this sample: {detection['killed']} KILLED and "
        f"{detection['confirmed_non_equivalent_survived']} SURVIVED; confirmed detection was "
        f"{detection['killed']}/{detection['denominator']} ({detection['percentage']:.1f}%).",
        f"- {combined['equivalent']} confirmed-equivalent evaluation was excluded from the detection denominator.", "",
        "## B02 operator counts", "",
    ]
    for row in operators:
        lines.append(f"- {row['operator']}: {row['evaluated']}/{row['selected']} evaluated; "
                     f"{row['survived']} SURVIVED, {row['killed']} KILLED, "
                     f"{row['equivalent']} EQUIVALENT, {row['non_evaluable']} non-evaluable; "
                     f"confirmed detection {row['detection_numerator']}/{row['detection_denominator']} "
                     f"({row['detection_percent']}%).")
    lines.extend(["", "## D027 accounting", ""])
    for row in d027:
        lines.append(f"- {row['state']}: {row['count']}/24 ({row['percent_of_cohort']}%).")
    RESULTS_NUMBERS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Matplotlib is required to generate paper figures; install it in the project environment before running this script.") from exc
    return plt


def _save(plt: Any, fig: Any, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / f"{stem}.png", dpi=240, facecolor="white")
    fig.savefig(FIGURE_DIR / f"{stem}.pdf", facecolor="white")
    plt.close(fig)


def _figures(result: dict[str, Any]) -> None:
    plt = _matplotlib()
    plt.rcParams.update({"font.size": 9, "axes.facecolor": "white", "figure.facecolor": "white"})
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    labels = ["Primary execution", "Primary + D027"]
    summaries = [result["primary"], result["combined"]]
    evaluated = [summary["evaluated"] for summary in summaries]
    non_evaluable = [summary["non-evaluable"] for summary in summaries]
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.bar(labels, evaluated, label="Evaluated", color=colors[0], hatch="///")
    ax.bar(labels, non_evaluable, bottom=evaluated, label="Non-evaluable", color=colors[1], hatch="...")
    for x, (yes, no) in enumerate(zip(evaluated, non_evaluable)):
        selected = summaries[x]["selected"]
        ax.text(x, yes / 2, f"{yes} ({percent(yes, selected)}%)", ha="center", va="center")
        ax.text(x, yes + no / 2, f"{no} ({percent(no, selected)}%)", ha="center", va="center")
    ax.set_title("Mutation evaluability before and after restoration")
    ax.set_ylabel("Repositories")
    ax.set_ylim(0, 43)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    _save(plt, fig, "evaluability_primary_vs_combined")

    summaries = [result["b02_by_operator"][operator] for operator in OPERATORS]
    segments = (("SURVIVED", "survived"), ("KILLED", "killed"),
                ("EQUIVALENT", "equivalent"), ("Non-evaluable", "non-evaluable"))
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    bottoms = [0] * 4
    for index, (label, key) in enumerate(segments):
        values = [summary[key] for summary in summaries]
        bars = ax.bar(OPERATORS, values, bottom=bottoms, label=label,
                      color=colors[index], hatch=("///", "xxx", "---", "...")[index])
        for bar, value, bottom in zip(bars, values, bottoms):
            if value:
                ax.text(bar.get_x() + bar.get_width() / 2, bottom + value / 2,
                        str(value), ha="center", va="center")
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
    for x, summary in enumerate(summaries):
        ax.text(x, summary["selected"] + 0.25, f"N={summary['selected']}", ha="center")
    ax.set_title("B02 mutation outcomes and evaluability by operator")
    ax.set_ylabel("Repositories")
    ax.set_ylim(0, 11.5)
    ax.tick_params(axis="x", rotation=15)
    ax.legend(frameon=False, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    _save(plt, fig, "b02_outcomes_by_operator")

    states = ["Evaluated after restoration", "Not restored after substantive attempt",
              "Report present, restoration not attempted", "No D027 report"]
    d = result["d027"]
    values = [d["mutation_evaluated"], d["not_restored"],
              d["restoration_not_attempted"], d["report_absent_not_attempted"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bars = ax.barh(states, values, color=colors[:4], hatch=["///", "xxx", "---", "..."])
    ax.invert_yaxis()
    for bar, value in zip(bars, values):
        ax.text(value + 0.15, bar.get_y() + bar.get_height() / 2,
                f"{value} ({percent(value, d['cohort'])}%)", va="center")
    ax.set_title("D027 restoration accounting")
    ax.set_xlabel("Cases")
    ax.set_xlim(0, 14)
    ax.spines[["top", "right"]].set_visible(False)
    _save(plt, fig, "d027_restoration_accounting")


def generate() -> list[Path]:
    result = calculate()
    _frozen_assertions(result)
    study, operators, d027 = build_rows(result)
    _write_text_assets(study, operators, d027, result)
    _figures(result)
    return list(EXPECTED_FILES)


if __name__ == "__main__":
    generated = generate()
    print(f"Generated {len(generated)} paper assets:")
    for path in generated:
        print(path.relative_to(ROOT))
