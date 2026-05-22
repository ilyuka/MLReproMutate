from sklearn.model_selection import StratifiedKFold


def run_experiment() -> int:
    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    return cv.get_n_splits()


if __name__ == "__main__":
    print(run_experiment())
