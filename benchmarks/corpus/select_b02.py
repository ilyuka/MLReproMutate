import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
POOL_ROOT = ROOT / "pools"
OUTPUT = ROOT / "sampling_frame.jsonl"

OPERATORS = [
    "random-seed",
    "dependency-pin",
    "data-split",
    "cv-fold-count",
]

PRIMARY_CAP = 10
SEED_PHRASE = "MLReproMutate-B02-primary-sampling-v1"


def load_pool(operator):
    path = POOL_ROOT / f"{operator}.jsonl"

    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows.sort(key=lambda row: row["pool_index"])

    expected = list(range(1, len(rows) + 1))
    observed = [row["pool_index"] for row in rows]

    if observed != expected:
        raise SystemExit(
            f"{operator}: non-sequential pool indexes: {observed}"
        )

    return rows


def operator_seed(operator):
    material = f"{SEED_PHRASE}|{operator}".encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()
    return int(digest[:16], 16), digest


pools = {
    operator: load_pool(operator)
    for operator in OPERATORS
}

# Verify raw repository uniqueness again before sampling.
raw_repositories = [
    row["repository"]
    for operator in OPERATORS
    for row in pools[operator]
]

if len(raw_repositories) != len(set(raw_repositories)):
    raise SystemExit(
        "Cross-pool duplicate repository detected."
    )

selected_by_operator = {}

for operator in OPERATORS:
    rows = pools[operator]
    n = min(PRIMARY_CAP, len(rows))

    if len(rows) <= PRIMARY_CAP:
        selected = list(rows)
        method = "census"
        seed = None
        digest = None
    else:
        seed, digest = operator_seed(operator)
        rng = random.Random(seed)
        selected = rng.sample(rows, n)
        selected.sort(key=lambda row: row["pool_index"])
        method = "random-sample"

    selected_by_operator[operator] = (
        selected,
        method,
        seed,
        digest,
    )

records = []
case_number = 1

for operator in OPERATORS:
    selected, method, seed, digest = selected_by_operator[operator]

    for row in selected:
        record = dict(row)

        record["case_id"] = f"B02-{case_number:02d}"
        record["source_pool_index"] = row["pool_index"]
        record["selection_method"] = method
        record["sampling_seed_phrase"] = SEED_PHRASE
        record["sampling_seed"] = seed
        record["sampling_seed_sha256"] = digest

        records.append(record)
        case_number += 1

selected_repositories = [
    row["repository"]
    for row in records
]

if len(selected_repositories) != len(set(selected_repositories)):
    raise SystemExit(
        "Duplicate repository in final B02 frame."
    )

OUTPUT.write_text(
    "".join(
        json.dumps(
            row,
            ensure_ascii=False,
            separators=(",", ":"),
        ) + "\n"
        for row in records
    ),
    encoding="utf-8",
)

print("B02 PRIMARY SELECTION")
print()

for operator in OPERATORS:
    selected, method, seed, digest = selected_by_operator[operator]

    print(
        f"{operator}: "
        f"pool={len(pools[operator])} "
        f"selected={len(selected)} "
        f"method={method}"
    )

    if seed is not None:
        print(f"  seed={seed}")
        print(
            "  selected_pool_indices="
            + ",".join(
                str(row["pool_index"])
                for row in selected
            )
        )

print()
print("TOTAL SELECTED:", len(records))
print(
    "UNIQUE REPOSITORIES:",
    len(set(selected_repositories)),
)
print("WROTE:", OUTPUT)
