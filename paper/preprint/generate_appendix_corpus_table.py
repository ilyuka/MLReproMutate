#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CORPUS = ROOT / "benchmarks" / "corpus"
RQ2 = CORPUS / "rq2"
OUT = HERE / "tables"

EXPECTED_IDS = (
    [f"B01-{i:02d}" for i in range(1, 11)]
    + [f"B02-{i:02d}" for i in range(1, 30)]
)


def load_final_accounting():
    path = CORPUS / "final_accounting.py"

    spec = importlib.util.spec_from_file_location(
        "mlrm_final_accounting",
        path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load final_accounting.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def read_jsonl(path: Path) -> list[dict]:
    rows = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))

    return rows


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def tex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }

    return "".join(replacements.get(ch, ch) for ch in value)


def tt(value: str) -> str:
    return rf"\texttt{{{tex_escape(value)}}}"


def breakable_tt(value: str) -> str:
    """Monospace text with explicit legal breaks after common separators."""
    parts = []
    chunk = []

    for ch in value:
        if ch in "/-_.":
            if chunk:
                parts.append(tt("".join(chunk)))
                chunk = []
            parts.append(tt(ch))
            parts.append(r"\allowbreak{}")
        else:
            chunk.append(ch)

    if chunk:
        parts.append(tt("".join(chunk)))

    return "".join(parts)


def display_oracle(value):
    if value is None:
        return "--"
    return breakable_tt(value)


def display_source(value: str) -> str:
    if value == "primary":
        return "primary"
    if value == "D027":
        return "D027"
    if value == "none":
        return "--"
    raise ValueError(f"Unexpected result source: {value!r}")


def display_outcome(row: dict) -> str:
    if not row["evaluated"]:
        return r"non-\allowbreak{}evaluable"

    value = row["outcome"]

    mapping = {
        "killed": r"\textsc{Killed}",
        "survived": r"\textsc{Survived}",
        "equivalent": r"\textsc{Equivalent}",
        "invalid": r"\textsc{Invalid}",
        "timeout": r"\textsc{Timeout}",
        "error": r"\textsc{Error}",
    }

    if value not in mapping:
        raise ValueError(
            f"{row['case_id']}: unexpected outcome {value!r}"
        )

    return mapping[value]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    accounting = load_final_accounting()
    cases = accounting.build_case_table(CORPUS)

    blind_path = RQ2 / "blind_case_evidence.jsonl"
    blind_rows = read_jsonl(blind_path)

    if len(cases) != 39:
        raise RuntimeError(
            f"final accounting returned {len(cases)} rows, expected 39"
        )

    if len(blind_rows) != 39:
        raise RuntimeError(
            f"blind RQ2 frame has {len(blind_rows)} rows, expected 39"
        )

    case_ids = [row["case_id"] for row in cases]
    blind_ids = [row["case_id"] for row in blind_rows]

    if case_ids != EXPECTED_IDS:
        raise RuntimeError(
            "Final-accounting case sequence differs from frozen 39-case frame"
        )

    if blind_ids != EXPECTED_IDS:
        raise RuntimeError(
            "Blind-frame case sequence differs from frozen 39-case frame"
        )

    blind_by_id = {
        row["case_id"]: row
        for row in blind_rows
    }

    if len(blind_by_id) != 39:
        raise RuntimeError("Duplicate case IDs in blind frame")

    joined = []

    for case in cases:
        case_id = case["case_id"]
        blind = blind_by_id[case_id]

        if blind["repository"] != case["repository"]:
            raise RuntimeError(
                f"{case_id}: repository mismatch between frozen layers"
            )

        joined.append({
            "case_id": case_id,
            "repository": case["repository"],
            "revision": blind["revision"],
            "operator": case["operator"],
            "workflow_kind": blind["workflow_kind"],
            "oracle_kind": blind["oracle_kind"],
            "result_source": case["combined_result_source"],
            "evaluated": case["combined_evaluated"],
            "outcome": case["combined_outcome"],
            "semantic_status": case["combined_semantic_status"],
        })

    # --------------------------------------------------------
    # Machine-readable appendix table
    # --------------------------------------------------------

    csv_path = OUT / "full_corpus.csv"

    fields = [
        "case_id",
        "repository",
        "revision",
        "operator",
        "workflow_kind",
        "oracle_kind",
        "result_source",
        "evaluated",
        "outcome",
        "semantic_status",
    ]

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(joined)

    # --------------------------------------------------------
    # Paper table
    # --------------------------------------------------------

    tex = []

    tex += [
        r"\begingroup",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{2pt}",
        r"\renewcommand{\arraystretch}{1.15}",
        r"\begin{longtable}{@{}"
        r">{\raggedright\arraybackslash}p{0.075\textwidth}"
        r">{\raggedright\arraybackslash}p{0.245\textwidth}"
        r">{\raggedright\arraybackslash}p{0.115\textwidth}"
        r">{\raggedright\arraybackslash}p{0.145\textwidth}"
        r">{\raggedright\arraybackslash}p{0.110\textwidth}"
        r">{\raggedright\arraybackslash}p{0.070\textwidth}"
        r">{\raggedright\arraybackslash}p{0.110\textwidth}"
        r"@{}}",
        r"\caption{Full frozen 39-case empirical corpus. "
        r"Oracle classification is shown only where it was prospectively "
        r"recorded for B02; B01 entries are left unclassified. "
        r"Source identifies whether the combined result comes from the "
        r"canonical primary execution or the bounded D027 restoration layer.}"
        r"\label{tab:full-corpus}\\",
        r"\toprule",
        r"\textbf{Case} &",
        r"\textbf{Repository} &",
        r"\textbf{Operator} &",
        r"\textbf{Workflow} &",
        r"\textbf{Oracle} &",
        r"\textbf{Source} &",
        r"\textbf{Outcome} \\",
        r"\midrule",
        r"\endfirsthead",
        r"",
        r"\multicolumn{7}{c}{"
        r"\tablename\ \thetable\ --- continued from previous page} \\",
        r"\toprule",
        r"\textbf{Case} &",
        r"\textbf{Repository} &",
        r"\textbf{Operator} &",
        r"\textbf{Workflow} &",
        r"\textbf{Oracle} &",
        r"\textbf{Source} &",
        r"\textbf{Outcome} \\",
        r"\midrule",
        r"\endhead",
        r"",
        r"\midrule",
        r"\multicolumn{7}{r}{Continued on next page} \\",
        r"\endfoot",
        r"",
        r"\bottomrule",
        r"\endlastfoot",
        r"",
    ]

    for row in joined:
        tex.append(
            f"{tt(row['case_id'])} & "
            f"{breakable_tt(row['repository'])} & "
            f"{breakable_tt(row['operator'])} & "
            f"{breakable_tt(row['workflow_kind'])} & "
            f"{display_oracle(row['oracle_kind'])} & "
            f"{display_source(row['result_source'])} & "
            f"{display_outcome(row)} \\\\"
        )

    tex += [
        r"\end{longtable}",
        r"\endgroup",
        "",
    ]

    tex_path = OUT / "table_full_corpus.tex"
    tex_path.write_text(
        "\n".join(tex),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest = {
        "rows": len(joined),
        "expected_case_ids": EXPECTED_IDS,
        "inputs": {
            "screening.jsonl": sha256(
                CORPUS / "screening.jsonl"
            ),
            "d027_restoration_cohort.jsonl": sha256(
                CORPUS / "d027_restoration_cohort.jsonl"
            ),
            "rq2/blind_case_evidence.jsonl": sha256(
                blind_path
            ),
        },
        "outputs": {
            "full_corpus.csv": sha256(csv_path),
            "table_full_corpus.tex": sha256(tex_path),
        },
    }

    manifest_path = OUT / "full_corpus_manifest.json"
    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print("FULL_CORPUS_ROWS=39")
    print(f"CSV={csv_path}")
    print(f"TEX={tex_path}")
    print(f"MANIFEST={manifest_path}")


if __name__ == "__main__":
    main()
