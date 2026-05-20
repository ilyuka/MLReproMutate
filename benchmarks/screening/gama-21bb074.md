# GAMA screening

Repository: amore-labs/gama

Revision:
21bb07461bbfcc516201dad3198669de04426a68

Target operator:
data-split

Applicable target:
examples/classification_example.py

Mutation applicability:
train_test_split(..., stratify=y, ...) -> stratify=None

Screening result:
SETUP_FAILED

Reason:
dependency_drift

Observed setup issues:

1. The declared dependency range allowed a NumPy 2.x installation together
   with an older scikit-learn release, producing a binary ABI incompatibility.

2. After applying a NumPy < 2 compatibility constraint, importing GAMA failed
   because the stopit dependency imports pkg_resources, which is not present
   in current setuptools releases.

No mutation evaluation was performed because a valid baseline environment was
not established.

This repository was not manually repaired further in accordance with the
screening stop rule.
