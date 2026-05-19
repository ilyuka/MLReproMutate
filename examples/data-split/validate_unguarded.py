from experiment import run_experiment

y_test = run_experiment()

if len(y_test) != 2:
    raise SystemExit(
        f"Expected two test samples, got {len(y_test)}."
    )

print(f"test_labels={y_test}")
