import json

from imbalance.pipeline import Pipeline
from sklearn.datasets import make_classification

x, y = make_classification(
    n_samples=120,
    n_features=8,
    n_informative=5,
    n_redundant=1,
    n_classes=2,
    weights=[0.5, 0.5],
    random_state=7,
)

pipeline = Pipeline(
    x,
    y,
    classifiers="lr",
    dataset_balance=[0.5],
    dataset_size=[1.0],
    n_permutations=0,
    rand_seed=42,
    n_init=1,
)

fold_count = pipeline.cross_validation.get_n_splits(
    x,
    y,
)

pipeline.evaluate()

scores = pipeline.scores[0.5][1.0]["LogisticRegression"]

output = {
    "fold_count": int(fold_count),
    "accuracy": float(scores["accuracy"][0]),
    "roc_auc": float(scores["roc_auc"][0]),
    "balanced_accuracy": float(
        scores["balanced_accuracy"][0]
    ),
    "f1": float(scores["f1"][0]),
}

print(json.dumps(output, sort_keys=True))
