from experiment import run_experiment

EXPECTED = 0.6394267984578837

value = run_experiment()

if value != EXPECTED:
    raise SystemExit(
        f"Expected reproducible value {EXPECTED}, got {value}."
    )

print(f"experiment_value={value}")
