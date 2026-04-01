"""Small deterministic ML-style experiment fixture."""


def run_experiment() -> float:
    """Return a deterministic placeholder experiment score."""
    features = [1.0, 2.0, 3.0, 4.0]
    labels = [0.0, 0.0, 1.0, 1.0]

    positive_mean = sum(
        feature
        for feature, label in zip(features, labels, strict=True)
        if label == 1.0
    ) / 2

    negative_mean = sum(
        feature
        for feature, label in zip(features, labels, strict=True)
        if label == 0.0
    ) / 2

    return positive_mean - negative_mean


if __name__ == "__main__":
    print(run_experiment())