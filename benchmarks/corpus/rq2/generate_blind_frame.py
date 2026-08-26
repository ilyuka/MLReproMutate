#!/usr/bin/env python3
"""Generate MLReproMutate's 39-case outcome-blind RQ2 evidence frame."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

B01_IDS = tuple(f"B01-{n:02d}" for n in range(1, 11))
B02_IDS = tuple(f"B02-{n:02d}" for n in range(1, 30))
ALL_IDS = B01_IDS + B02_IDS
WORKFLOWS = {
    "upstream-test", "ci", "documented-validation",
    "documented-experiment", "documented-example",
}
ORACLES = {
    "assertion", "metric-threshold", "reference-comparison", "completion-only",
}
EXPECTED_B02_ORACLES = {
    "completion-only": 22, "assertion": 7,
    "metric-threshold": 0, "reference-comparison": 0,
}
EXPECTED_B02_WORKFLOWS = {
    "upstream-test": 10, "documented-experiment": 9,
    "documented-example": 6, "documented-validation": 3, "ci": 1,
}
OUTPUT_KEYS = {
    "case_id", "batch", "schema_version", "repository", "revision",
    "workflow_kind", "workflow_command", "workflow_reference",
    "oracle_kind", "oracle_provenance", "oracle_strength_derived",
}
FORBIDDEN_KEY_BITS = {
    "mutation", "outcome", "baseline", "screening", "semantic", "restoration",
    "return_code", "report_path", "d027", "primary_status", "combined_result",
}
FORBIDDEN_TEXT = re.compile(
    r"\b(killed|survived|equivalent|confirmed-non-equivalent|"
    r"confirmed-equivalent|unverified|setup-failed|workflow-unavailable|"
    r"not-evaluated|evaluated|restored|not-restored)\b", re.I
)


class BlindFrameError(RuntimeError):
    pass


def jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise BlindFrameError(f"cannot read {path}: {exc}") from exc
    out = []
    for n, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BlindFrameError(f"{path}:{n}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise BlindFrameError(f"{path}:{n}: expected JSON object")
        out.append(row)
    return out


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise BlindFrameError(f"{label} must be a non-empty string")
    return value


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    except OSError as exc:
        raise BlindFrameError(f"cannot hash {path}: {exc}") from exc
    return h.hexdigest()


def workflow(row: dict[str, Any], label: str) -> tuple[str, str, str, str | None]:
    w = row.get("workflow")
    if not isinstance(w, dict):
        raise BlindFrameError(f"{label}: workflow must be an object")
    kind = text(w.get("kind"), f"{label}.workflow.kind")
    command = text(w.get("command"), f"{label}.workflow.command")
    reference = text(w.get("reference"), f"{label}.workflow.reference")
    oracle = w.get("oracle_kind")
    if kind not in WORKFLOWS:
        raise BlindFrameError(f"{label}: unknown workflow kind {kind!r}")
    if oracle is not None and oracle not in ORACLES:
        raise BlindFrameError(f"{label}: unknown oracle kind {oracle!r}")
    return kind, command, reference, oracle


def strength(oracle: str | None) -> str | None:
    if oracle is None:
        return None
    if oracle == "completion-only":
        return "completion-only"
    if oracle in {"assertion", "metric-threshold", "reference-comparison"}:
        return "substantive-oracle"
    raise BlindFrameError(f"unknown oracle {oracle!r}")


def check_b02(sample: dict[str, Any], screen: dict[str, Any], case_id: str):
    if sample.get("case_id") != case_id or screen.get("case_id") != case_id:
        raise BlindFrameError(f"{case_id}: case_id mismatch")
    if screen.get("schema_version") != 2 or screen.get("protocol_version") != "2.0":
        raise BlindFrameError(f"{case_id}: expected schema_version=2, protocol_version=2.0")

    for key in ("repository", "revision"):
        a = text(sample.get(key), f"{case_id}.sampling.{key}")
        b = text(screen.get(key), f"{case_id}.screening.{key}")
        if a != b:
            raise BlindFrameError(f"{case_id}: {key} differs between frozen sources")

    sk, sc, sr, so = workflow(screen, case_id)
    fk = text(sample.get("workflow_kind"), f"{case_id}.sampling.workflow_kind")
    fc = text(sample.get("workflow_command"), f"{case_id}.sampling.workflow_command")
    fr = text(sample.get("workflow_reference"), f"{case_id}.sampling.workflow_reference")
    fo = text(sample.get("oracle_kind"), f"{case_id}.sampling.oracle_kind")
    if fk not in WORKFLOWS or fo not in ORACLES:
        raise BlindFrameError(f"{case_id}: invalid prospective workflow/oracle value")

    for label, a, b in (
        ("workflow kind", fk, sk), ("workflow command", fc, sc),
        ("workflow reference", fr, sr), ("oracle kind", fo, so),
    ):
        if a != b:
            raise BlindFrameError(
                f"{case_id}: {label} differs between sampling_frame.jsonl "
                f"and screening.jsonl: {a!r} != {b!r}"
            )
    return fk, fc, fr, fo


def build(screening: list[dict[str, Any]], sampling: list[dict[str, Any]]):
    if len(screening) != 39:
        raise BlindFrameError(f"screening.jsonl has {len(screening)} rows; expected 39")
    if len(sampling) != 29:
        raise BlindFrameError(f"sampling_frame.jsonl has {len(sampling)} rows; expected 29")

    b01, b02 = screening[:10], screening[10:]
    if any(r.get("schema_version") != 1 for r in b01):
        raise BlindFrameError("first 10 screening rows must be schema-v1 B01")
    if any(r.get("schema_version") != 2 for r in b02):
        raise BlindFrameError("final 29 screening rows must be schema-v2 B02")

    rows = []
    # Schema-v1 B01 predates case_id; frozen screening order is B01-01..B01-10.
    # No mutation/report/D027 data are consulted for this mapping.
    for case_id, r in zip(B01_IDS, b01, strict=True):
        kind, command, reference, oracle = workflow(r, case_id)
        if oracle is not None:
            raise BlindFrameError(f"{case_id}: B01 unexpectedly contains oracle_kind")
        rows.append({
            "case_id": case_id, "batch": "B01", "schema_version": 1,
            "repository": text(r.get("repository"), f"{case_id}.repository"),
            "revision": text(r.get("revision"), f"{case_id}.revision"),
            "workflow_kind": kind, "workflow_command": command,
            "workflow_reference": reference, "oracle_kind": None,
            "oracle_provenance": "not-prospectively-recorded",
            "oracle_strength_derived": None,
        })

    sample_by_id = {}
    for r in sampling:
        cid = text(r.get("case_id"), "sampling.case_id")
        if cid in sample_by_id:
            raise BlindFrameError(f"duplicate sampling case_id {cid}")
        sample_by_id[cid] = r
    screen_by_id = {}
    for r in b02:
        cid = text(r.get("case_id"), "screening.case_id")
        if cid in screen_by_id:
            raise BlindFrameError(f"duplicate screening case_id {cid}")
        screen_by_id[cid] = r

    if tuple(sorted(sample_by_id)) != B02_IDS:
        raise BlindFrameError("sampling-frame IDs must be exactly B02-01..B02-29")
    if tuple(sorted(screen_by_id)) != B02_IDS:
        raise BlindFrameError("screening IDs must be exactly B02-01..B02-29")

    for cid in B02_IDS:
        s = sample_by_id[cid]
        kind, command, reference, oracle = check_b02(s, screen_by_id[cid], cid)
        rows.append({
            "case_id": cid, "batch": "B02", "schema_version": 2,
            "repository": text(s.get("repository"), f"{cid}.repository"),
            "revision": text(s.get("revision"), f"{cid}.revision"),
            "workflow_kind": kind, "workflow_command": command,
            "workflow_reference": reference, "oracle_kind": oracle,
            "oracle_provenance": "prospective-protocol-v2",
            "oracle_strength_derived": strength(oracle),
        })

    if tuple(r["case_id"] for r in rows) != ALL_IDS:
        raise BlindFrameError("generated order differs from frozen 39-case sequence")
    validate(rows)
    return rows


def validate(rows: list[dict[str, Any]]) -> None:
    if len(rows) != 39 or len({r["case_id"] for r in rows}) != 39:
        raise BlindFrameError("blind frame must contain exactly 39 unique cases")

    for r in rows:
        if set(r) != OUTPUT_KEYS:
            raise BlindFrameError(
                f"{r.get('case_id')}: output keys differ; "
                f"extra={sorted(set(r)-OUTPUT_KEYS)}, missing={sorted(OUTPUT_KEYS-set(r))}"
            )
        for key in r:
            if any(bit in key.lower() for bit in FORBIDDEN_KEY_BITS):
                raise BlindFrameError(f"{r['case_id']}: forbidden key {key!r}")
        for key, value in r.items():
            if isinstance(value, str):
                hit = FORBIDDEN_TEXT.search(value)
                if hit:
                    raise BlindFrameError(
                        f"{r['case_id']}: leaked token {hit.group(0)!r} in {key!r}"
                    )

    b01 = [r for r in rows if r["batch"] == "B01"]
    b02 = [r for r in rows if r["batch"] == "B02"]
    if len(b01) != 10 or len(b02) != 29:
        raise BlindFrameError(f"wrong batch counts: B01={len(b01)}, B02={len(b02)}")
    if any(r["oracle_kind"] is not None for r in b01):
        raise BlindFrameError("B01 oracle_kind must remain null")

    oc = Counter(r["oracle_kind"] for r in b02)
    observed_o = {k: oc.get(k, 0) for k in EXPECTED_B02_ORACLES}
    if observed_o != EXPECTED_B02_ORACLES:
        raise BlindFrameError(f"unexpected B02 oracle counts: {observed_o}")

    wc = Counter(r["workflow_kind"] for r in b02)
    observed_w = {k: wc.get(k, 0) for k in EXPECTED_B02_WORKFLOWS}
    if observed_w != EXPECTED_B02_WORKFLOWS:
        raise BlindFrameError(f"unexpected B02 workflow counts: {observed_w}")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    try:
        path.write_text(body, encoding="utf-8")
    except OSError as exc:
        raise BlindFrameError(f"cannot write {path}: {exc}") from exc


def write_manifest(path: Path, screening: Path, sampling: Path, output: Path, rows):
    b02 = [r for r in rows if r["batch"] == "B02"]
    data = {
        "artifact": "MLReproMutate RQ2 outcome-blind evidence frame",
        "case_count": 39,
        "batch_counts": {"B01": 10, "B02": 29},
        "b02_oracle_counts": dict(sorted(Counter(r["oracle_kind"] for r in b02).items())),
        "b02_workflow_counts": dict(sorted(Counter(r["workflow_kind"] for r in b02).items())),
        "inputs": {str(screening): sha256(screening), str(sampling): sha256(sampling)},
        "output": {"path": str(output), "sha256": sha256(output)},
        "blinding": {
            "operator_included": False,
            "outcome_fields_included": False,
            "semantic_verification_included": False,
            "baseline_results_included": False,
            "screening_execution_results_included": False,
            "restoration_results_included": False,
            "b01_oracle_kind": "not-prospectively-recorded",
            "b02_oracle_kind": "prospective-protocol-v2",
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args():
    default_corpus = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser(description="Generate the 39-case outcome-blind RQ2 frame")
    p.add_argument("--corpus-dir", type=Path, default=default_corpus)
    p.add_argument("--output", type=Path)
    p.add_argument("--manifest", type=Path)
    return p.parse_args()


def main() -> None:
    a = parse_args()
    corpus = a.corpus_dir.resolve()
    screening = corpus / "screening.jsonl"
    sampling = corpus / "sampling_frame.jsonl"
    output = a.output.resolve() if a.output else corpus / "rq2" / "blind_case_evidence.jsonl"
    manifest = a.manifest.resolve() if a.manifest else corpus / "rq2" / "blind_frame_manifest.json"

    rows = build(jsonl(screening), jsonl(sampling))
    write_jsonl(output, rows)
    written = jsonl(output)
    validate(written)  # validate the actual written file, not only in-memory rows
    write_manifest(manifest, screening, sampling, output, written)

    b02 = [r for r in written if r["batch"] == "B02"]
    print("RQ2 blind frame: OK")
    print("cases: 39 (B01=10, B02=29)")
    print("B02 oracle kinds:", dict(sorted(Counter(r["oracle_kind"] for r in b02).items())))
    print("B02 workflow kinds:", dict(sorted(Counter(r["workflow_kind"] for r in b02).items())))
    print("output:", output)
    print("output sha256:", sha256(output))
    print("manifest:", manifest)


if __name__ == "__main__":
    try:
        main()
    except BlindFrameError as exc:
        raise SystemExit(f"RQ2 blind-frame validation failed: {exc}") from exc
