from experiment import run_experiment

fold_count = run_experiment()

if fold_count < 2:
    raise SystemExit(
        f"Expected a valid cross-validation protocol, got {fold_count}."
    )

print(f"fold_count={fold_count}")
