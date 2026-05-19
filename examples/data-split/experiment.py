from sklearn.model_selection import train_test_split


def run_experiment() -> list[int]:
    X = ["sample-0", "sample-1", "sample-2", "sample-3"]
    y = [0, 0, 1, 1]

    _, _, _, y_test = train_test_split(
        X,
        y,
        test_size=0.5,
        random_state=42,
        stratify=y,
    )

    return y_test


if __name__ == "__main__":
    print(run_experiment())
