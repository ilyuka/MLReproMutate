from pathlib import Path

from experiment import run_experiment

score = run_experiment()

if score != 2.0:
    raise SystemExit(1)

requirements = Path("requirements.txt").read_text(encoding="utf-8")

if "scikit-learn==1.5.2" not in requirements:
    raise SystemExit(1)

raise SystemExit(0)