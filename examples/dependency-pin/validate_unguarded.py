from experiment import run_experiment


score = run_experiment()

if score != 2.0:
    raise SystemExit(1)

raise SystemExit(0)