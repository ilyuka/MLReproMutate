from experiment import run_experiment

EXPECTED_FOLDS = 5

fold_count = run_experiment()

if fold_count != EXPECTED_FOLDS:
    raise SystemExit(
        f"Expected {EXPECTED_FOLDS} folds, got {fold_count}."
    )

print(f"fold_count={fold_count}")
