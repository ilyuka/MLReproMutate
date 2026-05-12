from experiment import run_experiment

value = run_experiment()

if not 0.0 <= value < 1.0:
    raise SystemExit("Experiment produced an invalid value.")

print(f"experiment_value={value}")
