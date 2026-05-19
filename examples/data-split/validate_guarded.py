from experiment import run_experiment

y_test = run_experiment()

if sorted(y_test) != [0, 1]:
    raise SystemExit(
        "Expected stratified test labels [0, 1], "
        f"got {y_test}."
    )

print(f"test_labels={y_test}")
